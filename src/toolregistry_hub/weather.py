"""Weather information via wttr.in.

Provides current conditions and multi-day forecasts for any location
using the free wttr.in JSON API.  No API key required.
"""

from __future__ import annotations

import json
from typing import Literal

from ._vendor.httpclient import get as _http_get
from ._vendor.httpclient import HttpConnectionError, HTTPError, HttpTimeoutError
from ._vendor.structlog import get_logger

logger = get_logger()

_WTTR_BASE = "https://wttr.in"
_TIMEOUT = 10.0


class WeatherError(RuntimeError):
    """Raised when a weather request fails."""


def _fetch_json(location: str) -> dict:
    """Fetch wttr.in JSON for *location*.

    Args:
        location: City name, airport code, coordinates, etc.

    Returns:
        Parsed JSON dict from wttr.in ``?format=j1``.

    Raises:
        WeatherError: On network or API errors.
    """
    # Encode spaces for URL
    encoded = location.replace(" ", "+")
    url = f"{_WTTR_BASE}/{encoded}?format=j1"
    try:
        resp = _http_get(url, timeout=_TIMEOUT)
        resp.raise_for_status()
        return resp.json()
    except HttpTimeoutError:
        raise WeatherError(f"Request timed out for location: {location}")
    except (HTTPError, HttpConnectionError) as exc:
        raise WeatherError(f"Failed to fetch weather for '{location}': {exc}")
    except Exception as exc:
        raise WeatherError(f"Unexpected error fetching weather: {exc}")


def _extract_area(data: dict) -> dict[str, str]:
    """Extract nearest area info."""
    area = data.get("nearest_area", [{}])[0]
    return {
        "name": area.get("areaName", [{}])[0].get("value", ""),
        "region": area.get("region", [{}])[0].get("value", ""),
        "country": area.get("country", [{}])[0].get("value", ""),
        "latitude": area.get("latitude", ""),
        "longitude": area.get("longitude", ""),
    }


def _pick_temp(obj: dict, units: str) -> str:
    """Return temperature string with unit suffix."""
    if units == "imperial":
        for key in ("temp_F", "tempF"):
            if key in obj:
                return f"{obj[key]}°F"
        # Fallback: hourly uses 'tempF', current uses 'temp_F'
        return f"{obj.get('temp_F', obj.get('tempF', '?'))}°F"
    for key in ("temp_C", "tempC"):
        if key in obj:
            return f"{obj[key]}°C"
    return f"{obj.get('temp_C', obj.get('tempC', '?'))}°C"


def _pick_feels(obj: dict, units: str) -> str:
    """Return feels-like temperature string."""
    if units == "imperial":
        return f"{obj.get('FeelsLikeF', '?')}°F"
    return f"{obj.get('FeelsLikeC', '?')}°C"


def _pick_wind(obj: dict, units: str) -> str:
    """Return wind string."""
    direction = obj.get("winddir16Point", "")
    if units == "imperial":
        return f"{obj.get('windspeedMiles', '?')} mph {direction}".strip()
    return f"{obj.get('windspeedKmph', '?')} km/h {direction}".strip()


def _pick_precip(obj: dict, units: str) -> str:
    """Return precipitation string."""
    if units == "imperial":
        return f"{obj.get('precipInches', '0.0')} in"
    return f"{obj.get('precipMM', '0.0')} mm"


def _desc(obj: dict) -> str:
    """Extract weather description text."""
    descs = obj.get("weatherDesc", [{}])
    return descs[0].get("value", "") if descs else ""


def _build_current(data: dict, units: str) -> dict:
    """Build current conditions dict."""
    cc = data.get("current_condition", [{}])[0]
    return {
        "temperature": _pick_temp(cc, units),
        "feels_like": _pick_feels(cc, units),
        "description": _desc(cc),
        "humidity": f"{cc.get('humidity', '?')}%",
        "wind": _pick_wind(cc, units),
        "precipitation": _pick_precip(cc, units),
        "cloud_cover": f"{cc.get('cloudcover', '?')}%",
        "uv_index": cc.get("uvIndex", "?"),
        "visibility": (
            f"{cc.get('visibilityMiles', '?')} mi"
            if units == "imperial"
            else f"{cc.get('visibility', '?')} km"
        ),
        "pressure": (
            f"{cc.get('pressureInches', '?')} inHg"
            if units == "imperial"
            else f"{cc.get('pressure', '?')} hPa"
        ),
    }


def _build_hourly(hour: dict, units: str) -> dict:
    """Build a single hourly entry."""
    raw_time = hour.get("time", "0")
    # wttr.in returns time as "0", "300", "600", ..., "2100"
    hh = int(raw_time) // 100
    return {
        "time": f"{hh:02d}:00",
        "temperature": _pick_temp(hour, units),
        "feels_like": _pick_feels(hour, units),
        "description": _desc(hour),
        "humidity": f"{hour.get('humidity', '?')}%",
        "wind": _pick_wind(hour, units),
        "precipitation": _pick_precip(hour, units),
        "chance_of_rain": f"{hour.get('chanceofrain', '?')}%",
        "chance_of_snow": f"{hour.get('chanceofsnow', '?')}%",
    }


def _build_day(day: dict, units: str, include_hourly: bool) -> dict:
    """Build a single forecast day dict."""
    astro = day.get("astronomy", [{}])[0]
    result: dict = {
        "date": day.get("date", ""),
        "max_temp": (
            f"{day.get('maxtempF', '?')}°F"
            if units == "imperial"
            else f"{day.get('maxtempC', '?')}°C"
        ),
        "min_temp": (
            f"{day.get('mintempF', '?')}°F"
            if units == "imperial"
            else f"{day.get('mintempC', '?')}°C"
        ),
        "avg_temp": (
            f"{day.get('avgtempF', '?')}°F"
            if units == "imperial"
            else f"{day.get('avgtempC', '?')}°C"
        ),
        "uv_index": day.get("uvIndex", "?"),
        "total_snow_cm": day.get("totalSnow_cm", "0"),
        "sun_hours": day.get("sunHour", "?"),
        "sunrise": astro.get("sunrise", ""),
        "sunset": astro.get("sunset", ""),
        "moon_phase": astro.get("moon_phase", ""),
    }
    if include_hourly:
        result["hourly"] = [
            _build_hourly(h, units) for h in day.get("hourly", [])
        ]
    return result


class Weather:
    """Weather information powered by wttr.in.

    Provides current conditions and multi-day forecasts for any location.
    Supports city names, coordinates, airport codes (e.g. ``"JFK"``), and
    landmarks.  No API key required.

    Note: wttr.in is a free community service.  For safety-critical or
    high-frequency use, prefer an official weather API.
    """

    @staticmethod
    def get_current(
        location: str,
        units: Literal["metric", "imperial"] = "metric",
    ) -> str:
        """Get current weather conditions for a location.

        Returns temperature, feels-like, humidity, wind, precipitation,
        cloud cover, UV index, visibility, and pressure.

        Args:
            location: City name (e.g. ``"London"``), coordinates
                (e.g. ``"48.8566,2.3522"``), airport code (``"JFK"``),
                or landmark.  Use ``+`` or spaces for multi-word names.
            units: ``"metric"`` (°C, km/h, mm) or ``"imperial"``
                (°F, mph, in).  Defaults to ``"metric"``.

        Returns:
            JSON string with current conditions and resolved location.

        Raises:
            WeatherError: If the request fails.
        """
        data = _fetch_json(location)
        return json.dumps(
            {
                "location": _extract_area(data),
                "current": _build_current(data, units),
            },
            ensure_ascii=False,
        )

    @staticmethod
    def get_forecast(
        location: str,
        days: Literal[1, 2, 3] = 3,
        units: Literal["metric", "imperial"] = "metric",
        include_hourly: bool = False,
    ) -> str:
        """Get weather forecast for a location (up to 3 days).

        Each day includes high/low/average temperatures, UV index, snow,
        sun hours, sunrise/sunset, and moon phase.  Optionally includes
        3-hourly breakdowns.

        Args:
            location: City name, coordinates, airport code, or landmark.
            days: Number of forecast days (1–3).  Defaults to 3.
            units: ``"metric"`` or ``"imperial"``.  Defaults to ``"metric"``.
            include_hourly: If ``True``, include 3-hourly forecasts per day.
                Defaults to ``False`` to keep output compact.

        Returns:
            JSON string with location and daily forecasts.

        Raises:
            WeatherError: If the request fails.
        """
        data = _fetch_json(location)
        weather_days = data.get("weather", [])[:days]
        return json.dumps(
            {
                "location": _extract_area(data),
                "forecast": [
                    _build_day(d, units, include_hourly) for d in weather_days
                ],
            },
            ensure_ascii=False,
        )
