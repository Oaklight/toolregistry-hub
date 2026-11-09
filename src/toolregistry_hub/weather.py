"""Weather information via wttr.in.

Provides current conditions and multi-day forecasts for any location
using the free wttr.in JSON API.  No API key required.
"""

from __future__ import annotations

from typing import Any, Literal, TypedDict

from toolregistry import ToolTag

from ._metadata import tool_metadata
from ._vendor.httpclient import HttpConnectionError, HTTPError, HttpTimeoutError
from ._vendor.httpclient import get as _http_get
from ._vendor.structlog import get_logger

logger = get_logger()

_WTTR_BASE = "https://wttr.in"
_TIMEOUT = 10.0

# Declared result shapes, published as MCP outputSchema/structuredContent.
# Only tools whose result is a dict with stable keys declare one; the
# schemas name the keys a tool always emits, so no field is required and
# another key may appear.
_AREA_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "region": {"type": "string"},
        "country": {"type": "string"},
        "latitude": {"type": "string"},
        "longitude": {"type": "string"},
    },
    "additionalProperties": True,
}

#: One hour inside a forecast day (only present with ``include_hourly``).
_HOURLY_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "time": {"type": "string"},
        "temperature": {"type": "string"},
        "feels_like": {"type": "string"},
        "description": {"type": "string"},
        "humidity": {"type": "string"},
        "wind": {"type": "string"},
        "precipitation": {"type": "string"},
        "chance_of_rain": {"type": "string"},
        "chance_of_snow": {"type": "string"},
    },
    "additionalProperties": True,
}

#: One day inside a forecast.
_DAY_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "date": {"type": "string"},
        "max_temp": {"type": "string"},
        "min_temp": {"type": "string"},
        "avg_temp": {"type": "string"},
        "uv_index": {"type": ["string", "integer"]},
        "total_snow_cm": {"type": ["string", "number"]},
        "sun_hours": {"type": ["string", "number"]},
        "sunrise": {"type": "string"},
        "sunset": {"type": "string"},
        "moon_phase": {"type": "string"},
        "hourly": {"type": "array", "items": _HOURLY_SCHEMA},
    },
    "additionalProperties": True,
}

_CURRENT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "temperature": {"type": "string"},
        "feels_like": {"type": "string"},
        "description": {"type": "string"},
        "humidity": {"type": "string"},
        "wind": {"type": "string"},
        "precipitation": {"type": "string"},
        "cloud_cover": {"type": "string"},
        "uv_index": {"type": ["string", "integer"]},
        "visibility": {"type": "string"},
        "pressure": {"type": "string"},
    },
    "additionalProperties": True,
}


class Area(TypedDict, total=False):
    """Resolved location, as published by ``location``."""

    name: str
    region: str
    country: str
    latitude: str
    longitude: str


class CurrentConditions(TypedDict, total=False):
    """The ``current`` block of a current-weather result."""

    temperature: str
    feels_like: str
    description: str
    humidity: str
    wind: str
    precipitation: str
    cloud_cover: str
    uv_index: str | int
    visibility: str
    pressure: str


class Hourly(TypedDict, total=False):
    """One 3-hourly entry inside a forecast day."""

    time: str
    temperature: str
    feels_like: str
    description: str
    humidity: str
    wind: str
    precipitation: str
    chance_of_rain: str
    chance_of_snow: str


class ForecastDay(TypedDict, total=False):
    """One day inside a forecast."""

    date: str
    max_temp: str
    min_temp: str
    avg_temp: str
    uv_index: str | int
    total_snow_cm: str | float
    sun_hours: str | float
    sunrise: str
    sunset: str
    moon_phase: str
    hourly: list[Hourly]


class CurrentWeather(TypedDict, total=False):
    """Result of ``Weather.get_current``."""

    location: Area
    current: CurrentConditions


class Forecast(TypedDict, total=False):
    """Result of ``Weather.get_forecast``."""

    location: Area
    forecast: list[ForecastDay]


class Astronomy(TypedDict, total=False):
    """Result of ``Weather.get_astronomy``."""

    location: Area
    date: str
    sunrise: str
    sunset: str
    moonrise: str
    moonset: str
    moon_phase: str
    moon_illumination: str


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
    # Normalise input and encode spaces for URL
    encoded = location.strip().replace(" ", "+")
    url = f"{_WTTR_BASE}/{encoded}?format=j1"
    try:
        resp = _http_get(url, timeout=_TIMEOUT)
        resp.raise_for_status()
        return resp.json()  # ty: ignore[unresolved-attribute]
    except HttpTimeoutError as exc:
        raise WeatherError(f"Request timed out for location: {location}") from exc
    except (HTTPError, HttpConnectionError) as exc:
        raise WeatherError(f"Failed to fetch weather for '{location}': {exc}") from exc
    except Exception as exc:
        raise WeatherError(f"Unexpected error fetching weather: {exc}") from exc


def _extract_area(data: dict) -> Area:
    """Extract nearest area info."""
    area = data.get("nearest_area", [{}])[0]
    return Area(
        name=area.get("areaName", [{}])[0].get("value", ""),
        region=area.get("region", [{}])[0].get("value", ""),
        country=area.get("country", [{}])[0].get("value", ""),
        latitude=area.get("latitude", ""),
        longitude=area.get("longitude", ""),
    )


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


def _build_current(data: dict, units: str) -> CurrentConditions:
    """Build current conditions dict."""
    cc = data.get("current_condition", [{}])[0]
    return CurrentConditions(
        temperature=_pick_temp(cc, units),
        feels_like=_pick_feels(cc, units),
        description=_desc(cc),
        humidity=f"{cc.get('humidity', '?')}%",
        wind=_pick_wind(cc, units),
        precipitation=_pick_precip(cc, units),
        cloud_cover=f"{cc.get('cloudcover', '?')}%",
        uv_index=cc.get("uvIndex", "?"),
        visibility=(
            f"{cc.get('visibilityMiles', '?')} mi"
            if units == "imperial"
            else f"{cc.get('visibility', '?')} km"
        ),
        pressure=(
            f"{cc.get('pressureInches', '?')} inHg"
            if units == "imperial"
            else f"{cc.get('pressure', '?')} hPa"
        ),
    )


def _build_hourly(hour: dict, units: str) -> Hourly:
    """Build a single hourly entry."""
    raw_time = hour.get("time", "0")
    # wttr.in returns time as "0", "300", "600", ..., "2100"
    hh = int(raw_time) // 100
    return Hourly(
        time=f"{hh:02d}:00",
        temperature=_pick_temp(hour, units),
        feels_like=_pick_feels(hour, units),
        description=_desc(hour),
        humidity=f"{hour.get('humidity', '?')}%",
        wind=_pick_wind(hour, units),
        precipitation=_pick_precip(hour, units),
        chance_of_rain=f"{hour.get('chanceofrain', '?')}%",
        chance_of_snow=f"{hour.get('chanceofsnow', '?')}%",
    )


def _build_day(day: dict, units: str, include_hourly: bool) -> ForecastDay:
    """Build a single forecast day dict."""
    astro = day.get("astronomy", [{}])[0]
    result: ForecastDay = {
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
        result["hourly"] = [_build_hourly(h, units) for h in day.get("hourly", [])]
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
    @tool_metadata(
        defer=True,
        tags={ToolTag.NETWORK, ToolTag.READ_ONLY},
        read_only_hint=True,
        idempotent_hint=False,
        open_world_hint=True,
        title="Current Weather",
        extra={
            "output_schema": {
                "type": "object",
                "properties": {
                    "location": _AREA_SCHEMA,
                    "current": _CURRENT_SCHEMA,
                },
                "additionalProperties": True,
            }
        },
    )
    def get_current(
        location: str,
        units: Literal["metric", "imperial"] = "metric",
    ) -> CurrentWeather:
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
            Dict with ``location`` (resolved area info) and ``current``
            (temperature, feels_like, description, humidity, wind, etc.).

        Raises:
            WeatherError: If the request fails.
        """
        data = _fetch_json(location)
        return CurrentWeather(
            location=_extract_area(data),
            current=_build_current(data, units),
        )

    @staticmethod
    @tool_metadata(
        defer=True,
        tags={ToolTag.NETWORK, ToolTag.READ_ONLY},
        read_only_hint=True,
        idempotent_hint=False,
        open_world_hint=True,
        title="Weather Forecast",
        extra={
            "output_schema": {
                "type": "object",
                "properties": {
                    "location": _AREA_SCHEMA,
                    "forecast": {"type": "array", "items": _DAY_SCHEMA},
                },
                "additionalProperties": True,
            }
        },
    )
    def get_forecast(
        location: str,
        days: Literal[1, 2, 3] = 3,
        units: Literal["metric", "imperial"] = "metric",
        include_hourly: bool = False,
    ) -> Forecast:
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
            Dict with ``location`` and ``forecast`` (list of daily entries
            with max/min/avg temps, UV, snow, sun hours, sunrise/sunset,
            moon phase, and optional hourly breakdowns).

        Raises:
            WeatherError: If the request fails.
        """
        data = _fetch_json(location)
        weather_days = data.get("weather", [])[:days]
        return Forecast(
            location=_extract_area(data),
            forecast=[_build_day(d, units, include_hourly) for d in weather_days],
        )

    @staticmethod
    @tool_metadata(
        defer=True,
        tags={ToolTag.NETWORK, ToolTag.READ_ONLY},
        read_only_hint=True,
        idempotent_hint=False,
        open_world_hint=True,
        title="Astronomy",
        extra={
            "output_schema": {
                "type": "object",
                "properties": {
                    "location": _AREA_SCHEMA,
                    "date": {"type": "string"},
                    "sunrise": {"type": "string"},
                    "sunset": {"type": "string"},
                    "moonrise": {"type": "string"},
                    "moonset": {"type": "string"},
                    "moon_phase": {"type": "string"},
                    "moon_illumination": {"type": "string"},
                },
                "additionalProperties": True,
            }
        },
    )
    def get_astronomy(
        location: str,
    ) -> Astronomy:
        """Get astronomy data for a location (sunrise, sunset, moon phase).

        Returns today's astronomical information.  Useful for checking
        sunrise/sunset times, day/night status, or current moon phase
        without fetching the full forecast.

        Args:
            location: City name, coordinates, airport code, or landmark.

        Returns:
            Dict with ``location``, ``date``, ``sunrise``, ``sunset``,
            ``moonrise``, ``moonset``, ``moon_phase``, and
            ``moon_illumination``.

        Raises:
            WeatherError: If the request fails or no data is available.
        """
        data = _fetch_json(location)
        weather_days = data.get("weather", [])
        if not weather_days:
            raise WeatherError(f"No astronomy data available for: {location}")

        today = weather_days[0]
        astro_list = today.get("astronomy", [])
        if not astro_list:
            raise WeatherError(f"No astronomy data available for: {location}")

        astro = astro_list[0]
        return Astronomy(
            location=_extract_area(data),
            date=today.get("date", ""),
            sunrise=astro.get("sunrise", ""),
            sunset=astro.get("sunset", ""),
            moonrise=astro.get("moonrise", ""),
            moonset=astro.get("moonset", ""),
            moon_phase=astro.get("moon_phase", ""),
            moon_illumination=f"{astro.get('moon_illumination', '?')}%",
        )
