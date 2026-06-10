"""Unit tests for Weather module."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from toolregistry_hub.weather import Weather, WeatherError, _fetch_json

# ---------------------------------------------------------------------------
# Sample wttr.in JSON response (trimmed to essentials)
# ---------------------------------------------------------------------------
_SAMPLE_RESPONSE: dict = {
    "current_condition": [
        {
            "FeelsLikeC": "32",
            "FeelsLikeF": "90",
            "cloudcover": "25",
            "humidity": "63",
            "observation_time": "02:00 AM",
            "precipInches": "0.0",
            "precipMM": "0.0",
            "pressure": "1013",
            "pressureInches": "30",
            "temp_C": "29",
            "temp_F": "85",
            "uvIndex": "5",
            "visibility": "16",
            "visibilityMiles": "9",
            "weatherCode": "116",
            "weatherDesc": [{"value": "Partly cloudy"}],
            "weatherIconUrl": [{"value": "https://example.com/icon.png"}],
            "winddir16Point": "E",
            "winddirDegree": "98",
            "windspeedKmph": "5",
            "windspeedMiles": "3",
        }
    ],
    "nearest_area": [
        {
            "areaName": [{"value": "Chicago"}],
            "country": [{"value": "United States of America"}],
            "latitude": "41.894",
            "longitude": "-87.626",
            "population": "0",
            "region": [{"value": "Illinois"}],
            "weatherUrl": [{"value": "https://example.com"}],
        }
    ],
    "request": [{"query": "Lat 41.88 and Lon -87.62", "type": "LatLon"}],
    "weather": [
        {
            "astronomy": [
                {
                    "moon_illumination": "44",
                    "moon_phase": "Waning Crescent",
                    "moonrise": "01:27 AM",
                    "moonset": "02:12 PM",
                    "sunrise": "05:15 AM",
                    "sunset": "08:24 PM",
                }
            ],
            "avgtempC": "21",
            "avgtempF": "70",
            "date": "2026-06-09",
            "maxtempC": "30",
            "maxtempF": "86",
            "mintempC": "18",
            "mintempF": "64",
            "sunHour": "14.2",
            "totalSnow_cm": "0.0",
            "uvIndex": "7",
            "hourly": [
                {
                    "tempC": "22",
                    "tempF": "72",
                    "FeelsLikeC": "24",
                    "FeelsLikeF": "75",
                    "humidity": "60",
                    "windspeedKmph": "10",
                    "windspeedMiles": "6",
                    "winddir16Point": "NE",
                    "precipMM": "0.0",
                    "precipInches": "0.0",
                    "chanceofrain": "10",
                    "chanceofsnow": "0",
                    "weatherDesc": [{"value": "Sunny"}],
                    "time": "0",
                },
                {
                    "tempC": "25",
                    "tempF": "77",
                    "FeelsLikeC": "27",
                    "FeelsLikeF": "81",
                    "humidity": "55",
                    "windspeedKmph": "12",
                    "windspeedMiles": "7",
                    "winddir16Point": "E",
                    "precipMM": "0.1",
                    "precipInches": "0.0",
                    "chanceofrain": "20",
                    "chanceofsnow": "0",
                    "weatherDesc": [{"value": "Partly cloudy"}],
                    "time": "600",
                },
            ],
        },
        {
            "astronomy": [
                {
                    "moon_illumination": "35",
                    "moon_phase": "Waning Crescent",
                    "moonrise": "02:10 AM",
                    "moonset": "03:00 PM",
                    "sunrise": "05:15 AM",
                    "sunset": "08:25 PM",
                }
            ],
            "avgtempC": "23",
            "avgtempF": "73",
            "date": "2026-06-10",
            "maxtempC": "32",
            "maxtempF": "90",
            "mintempC": "19",
            "mintempF": "66",
            "sunHour": "13.8",
            "totalSnow_cm": "0.0",
            "uvIndex": "8",
            "hourly": [],
        },
        {
            "astronomy": [
                {
                    "moon_illumination": "25",
                    "moon_phase": "Waning Crescent",
                    "moonrise": "03:00 AM",
                    "moonset": "03:45 PM",
                    "sunrise": "05:15 AM",
                    "sunset": "08:25 PM",
                }
            ],
            "avgtempC": "20",
            "avgtempF": "68",
            "date": "2026-06-11",
            "maxtempC": "28",
            "maxtempF": "82",
            "mintempC": "16",
            "mintempF": "61",
            "sunHour": "12.5",
            "totalSnow_cm": "0.0",
            "uvIndex": "6",
            "hourly": [],
        },
    ],
}


def _mock_response(data: dict) -> MagicMock:
    """Build a mock Response that behaves like httpclient.Response."""
    resp = MagicMock()
    resp.status_code = 200
    resp.json.return_value = data
    resp.raise_for_status.return_value = None
    return resp


# ---------------------------------------------------------------------------
# get_current
# ---------------------------------------------------------------------------
class TestGetCurrent:
    @patch("toolregistry_hub.weather._http_get")
    def test_metric(self, mock_get: MagicMock):
        mock_get.return_value = _mock_response(_SAMPLE_RESPONSE)

        result = Weather.get_current("Chicago")

        assert result["location"]["name"] == "Chicago"
        assert result["location"]["country"] == "United States of America"
        cur = result["current"]
        assert cur["temperature"] == "29°C"
        assert cur["feels_like"] == "32°C"
        assert cur["description"] == "Partly cloudy"
        assert cur["humidity"] == "63%"
        assert "km/h" in cur["wind"]
        assert cur["precipitation"] == "0.0 mm"

    @patch("toolregistry_hub.weather._http_get")
    def test_imperial(self, mock_get: MagicMock):
        mock_get.return_value = _mock_response(_SAMPLE_RESPONSE)

        result = Weather.get_current("Chicago", units="imperial")

        cur = result["current"]
        assert cur["temperature"] == "85°F"
        assert cur["feels_like"] == "90°F"
        assert "mph" in cur["wind"]
        assert cur["precipitation"] == "0.0 in"
        assert "mi" in cur["visibility"]
        assert "inHg" in cur["pressure"]

    @patch("toolregistry_hub.weather._http_get")
    def test_url_encoding(self, mock_get: MagicMock):
        mock_get.return_value = _mock_response(_SAMPLE_RESPONSE)

        Weather.get_current("New York")

        called_url = mock_get.call_args[0][0]
        assert "New+York" in called_url

    @patch("toolregistry_hub.weather._http_get")
    def test_network_error(self, mock_get: MagicMock):
        from toolregistry_hub._vendor.httpclient import HttpConnectionError

        mock_get.side_effect = HttpConnectionError("Connection refused")

        with pytest.raises(WeatherError, match="Failed to fetch"):
            Weather.get_current("Nowhere")


# ---------------------------------------------------------------------------
# get_forecast
# ---------------------------------------------------------------------------
class TestGetForecast:
    @patch("toolregistry_hub.weather._http_get")
    def test_default_3_days(self, mock_get: MagicMock):
        mock_get.return_value = _mock_response(_SAMPLE_RESPONSE)

        result = Weather.get_forecast("Chicago")

        assert len(result["forecast"]) == 3
        day0 = result["forecast"][0]
        assert day0["date"] == "2026-06-09"
        assert day0["max_temp"] == "30°C"
        assert day0["min_temp"] == "18°C"
        assert day0["sunrise"] == "05:15 AM"
        assert day0["sunset"] == "08:24 PM"
        # By default, hourly should not be included
        assert "hourly" not in day0

    @patch("toolregistry_hub.weather._http_get")
    def test_1_day(self, mock_get: MagicMock):
        mock_get.return_value = _mock_response(_SAMPLE_RESPONSE)

        result = Weather.get_forecast("Chicago", days=1)

        assert len(result["forecast"]) == 1

    @patch("toolregistry_hub.weather._http_get")
    def test_imperial(self, mock_get: MagicMock):
        mock_get.return_value = _mock_response(_SAMPLE_RESPONSE)

        result = Weather.get_forecast("Chicago", units="imperial")

        day0 = result["forecast"][0]
        assert day0["max_temp"] == "86°F"
        assert day0["min_temp"] == "64°F"

    @patch("toolregistry_hub.weather._http_get")
    def test_include_hourly(self, mock_get: MagicMock):
        mock_get.return_value = _mock_response(_SAMPLE_RESPONSE)

        result = Weather.get_forecast("Chicago", days=1, include_hourly=True)

        day0 = result["forecast"][0]
        assert "hourly" in day0
        assert len(day0["hourly"]) == 2
        h0 = day0["hourly"][0]
        assert h0["time"] == "00:00"
        assert h0["temperature"] == "22°C"
        assert h0["description"] == "Sunny"
        assert h0["chance_of_rain"] == "10%"

    @patch("toolregistry_hub.weather._http_get")
    def test_timeout_error(self, mock_get: MagicMock):
        from toolregistry_hub._vendor.httpclient import HttpTimeoutError

        mock_get.side_effect = HttpTimeoutError("Timed out")

        with pytest.raises(WeatherError, match="timed out"):
            Weather.get_forecast("Nowhere")


# ---------------------------------------------------------------------------
# _fetch_json edge cases
# ---------------------------------------------------------------------------
class TestFetchJson:
    @patch("toolregistry_hub.weather._http_get")
    def test_http_error(self, mock_get: MagicMock):
        from toolregistry_hub._vendor.httpclient import HTTPError

        resp = MagicMock()
        resp.raise_for_status.side_effect = HTTPError(
            404, "Not Found", "https://wttr.in/UnknownPlace?format=j1"
        )
        mock_get.return_value = resp

        with pytest.raises(WeatherError, match="Failed to fetch"):
            _fetch_json("UnknownPlace")

    @patch("toolregistry_hub.weather._http_get")
    def test_json_decode_error(self, mock_get: MagicMock):
        resp = MagicMock()
        resp.raise_for_status.return_value = None
        resp.json.side_effect = ValueError("Invalid JSON")
        mock_get.return_value = resp

        with pytest.raises(WeatherError, match="Unexpected error"):
            _fetch_json("BadResponse")


# ---------------------------------------------------------------------------
# Registration sanity check
# ---------------------------------------------------------------------------
class TestRegistration:
    def test_weather_in_default_tools(self):
        """Weather should be listed in the hub's default tool list."""
        pytest.importorskip("toolregistry")
        from toolregistry_hub.server.registry import _DEFAULT_TOOLS

        namespaces = [s.namespace for s in _DEFAULT_TOOLS]
        assert "weather" in namespaces

    def test_weather_metadata(self):
        """Weather should have NETWORK + READ_ONLY tags."""
        pytest.importorskip("toolregistry")
        from toolregistry.tool import ToolTag

        from toolregistry_hub.server.registry import _TOOL_METADATA

        meta = _TOOL_METADATA.get("weather", {})
        assert ToolTag.NETWORK in meta.get("tags", set())
        assert ToolTag.READ_ONLY in meta.get("tags", set())


# ---------------------------------------------------------------------------
# get_astronomy
# ---------------------------------------------------------------------------
class TestGetAstronomy:
    @patch("toolregistry_hub.weather._http_get")
    def test_basic(self, mock_get: MagicMock):
        mock_get.return_value = _mock_response(_SAMPLE_RESPONSE)

        result = Weather.get_astronomy("Chicago")

        assert result["location"]["name"] == "Chicago"
        assert result["date"] == "2026-06-09"
        assert result["sunrise"] == "05:15 AM"
        assert result["sunset"] == "08:24 PM"
        assert result["moon_phase"] == "Waning Crescent"
        assert result["moon_illumination"] == "44%"
        assert result["moonrise"] == "01:27 AM"
        assert result["moonset"] == "02:12 PM"

    @patch("toolregistry_hub.weather._http_get")
    def test_no_weather_data(self, mock_get: MagicMock):
        data = dict(_SAMPLE_RESPONSE)
        data["weather"] = []
        mock_get.return_value = _mock_response(data)

        with pytest.raises(WeatherError, match="No astronomy data"):
            Weather.get_astronomy("Nowhere")

    @patch("toolregistry_hub.weather._http_get")
    def test_empty_astronomy(self, mock_get: MagicMock):
        data = dict(_SAMPLE_RESPONSE)
        data["weather"] = [{"date": "2026-06-09", "astronomy": []}]
        mock_get.return_value = _mock_response(data)

        with pytest.raises(WeatherError, match="No astronomy data"):
            Weather.get_astronomy("Nowhere")
