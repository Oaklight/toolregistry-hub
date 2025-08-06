"""Unit tests for UnitConverter module."""

import pytest
from toolregistry_hub.unit_converter import UnitConverter


class TestUnitConverter:
    """Test cases for UnitConverter class."""

    # Temperature conversions
    def test_celsius_to_fahrenheit(self):
        """Test Celsius to Fahrenheit conversion."""
        assert UnitConverter.celsius_to_fahrenheit(0) == 32
        assert UnitConverter.celsius_to_fahrenheit(100) == 212
        assert UnitConverter.celsius_to_fahrenheit(-40) == -40
        assert UnitConverter.celsius_to_fahrenheit(25) == pytest.approx(77)

    def test_fahrenheit_to_celsius(self):
        """Test Fahrenheit to Celsius conversion."""
        assert UnitConverter.fahrenheit_to_celsius(32) == 0
        assert UnitConverter.fahrenheit_to_celsius(212) == 100
        assert UnitConverter.fahrenheit_to_celsius(-40) == -40
        assert UnitConverter.fahrenheit_to_celsius(77) == pytest.approx(25)

    def test_kelvin_to_celsius(self):
        """Test Kelvin to Celsius conversion."""
        assert UnitConverter.kelvin_to_celsius(273.15) == 0
        assert UnitConverter.kelvin_to_celsius(373.15) == 100
        assert UnitConverter.kelvin_to_celsius(0) == -273.15

    def test_celsius_to_kelvin(self):
        """Test Celsius to Kelvin conversion."""
        assert UnitConverter.celsius_to_kelvin(0) == 273.15
        assert UnitConverter.celsius_to_kelvin(100) == 373.15
        assert UnitConverter.celsius_to_kelvin(-273.15) == 0

    # Length conversions
    def test_meters_to_feet(self):
        """Test meters to feet conversion."""
        assert UnitConverter.meters_to_feet(1) == pytest.approx(3.28084)
        assert UnitConverter.meters_to_feet(0) == 0
        assert UnitConverter.meters_to_feet(10) == pytest.approx(32.8084)

    def test_feet_to_meters(self):
        """Test feet to meters conversion."""
        assert UnitConverter.feet_to_meters(3.28084) == pytest.approx(1)
        assert UnitConverter.feet_to_meters(0) == 0
        assert UnitConverter.feet_to_meters(10) == pytest.approx(3.048, rel=1e-3)

    def test_centimeters_to_inches(self):
        """Test centimeters to inches conversion."""
        assert UnitConverter.centimeters_to_inches(2.54) == pytest.approx(1)
        assert UnitConverter.centimeters_to_inches(0) == 0
        assert UnitConverter.centimeters_to_inches(10) == pytest.approx(3.937, rel=1e-3)

    def test_inches_to_centimeters(self):
        """Test inches to centimeters conversion."""
        assert UnitConverter.inches_to_centimeters(1) == 2.54
        assert UnitConverter.inches_to_centimeters(0) == 0
        assert UnitConverter.inches_to_centimeters(12) == 30.48

    # Weight conversions
    def test_kilograms_to_pounds(self):
        """Test kilograms to pounds conversion."""
        assert UnitConverter.kilograms_to_pounds(1) == pytest.approx(2.20462)
        assert UnitConverter.kilograms_to_pounds(0) == 0
        assert UnitConverter.kilograms_to_pounds(10) == pytest.approx(22.0462)

    def test_pounds_to_kilograms(self):
        """Test pounds to kilograms conversion."""
        assert UnitConverter.pounds_to_kilograms(2.20462) == pytest.approx(1)
        assert UnitConverter.pounds_to_kilograms(0) == 0
        assert UnitConverter.pounds_to_kilograms(10) == pytest.approx(4.536, rel=1e-3)

    # Time conversions
    def test_seconds_to_minutes(self):
        """Test seconds to minutes conversion."""
        assert UnitConverter.seconds_to_minutes(60) == 1
        assert UnitConverter.seconds_to_minutes(0) == 0
        assert UnitConverter.seconds_to_minutes(120) == 2
        assert UnitConverter.seconds_to_minutes(30) == 0.5

    def test_minutes_to_seconds(self):
        """Test minutes to seconds conversion."""
        assert UnitConverter.minutes_to_seconds(1) == 60
        assert UnitConverter.minutes_to_seconds(0) == 0
        assert UnitConverter.minutes_to_seconds(2) == 120
        assert UnitConverter.minutes_to_seconds(0.5) == 30

    # Capacity conversions
    def test_liters_to_gallons(self):
        """Test liters to gallons conversion."""
        assert UnitConverter.liters_to_gallons(3.78541) == pytest.approx(1)
        assert UnitConverter.liters_to_gallons(0) == 0
        assert UnitConverter.liters_to_gallons(10) == pytest.approx(2.642, rel=1e-3)

    def test_gallons_to_liters(self):
        """Test gallons to liters conversion."""
        assert UnitConverter.gallons_to_liters(1) == pytest.approx(3.78541)
        assert UnitConverter.gallons_to_liters(0) == 0
        assert UnitConverter.gallons_to_liters(5) == pytest.approx(18.927, rel=1e-3)

    # Area conversions
    def test_square_meters_to_square_feet(self):
        """Test square meters to square feet conversion."""
        assert UnitConverter.square_meters_to_square_feet(1) == pytest.approx(10.7639)
        assert UnitConverter.square_meters_to_square_feet(0) == 0
        assert UnitConverter.square_meters_to_square_feet(10) == pytest.approx(107.639)

    def test_square_feet_to_square_meters(self):
        """Test square feet to square meters conversion."""
        assert UnitConverter.square_feet_to_square_meters(10.7639) == pytest.approx(1)
        assert UnitConverter.square_feet_to_square_meters(0) == 0
        assert UnitConverter.square_feet_to_square_meters(100) == pytest.approx(9.29, rel=1e-2)

    # Speed conversions
    def test_kmh_to_mph(self):
        """Test kilometers per hour to miles per hour conversion."""
        assert UnitConverter.kmh_to_mph(1.60934) == pytest.approx(1)
        assert UnitConverter.kmh_to_mph(0) == 0
        assert UnitConverter.kmh_to_mph(100) == pytest.approx(62.137, rel=1e-3)

    def test_mph_to_kmh(self):
        """Test miles per hour to kilometers per hour conversion."""
        assert UnitConverter.mph_to_kmh(1) == pytest.approx(1.60934)
        assert UnitConverter.mph_to_kmh(0) == 0
        assert UnitConverter.mph_to_kmh(60) == pytest.approx(96.56, rel=1e-2)

    # Data storage conversions
    def test_bits_to_bytes(self):
        """Test bits to bytes conversion."""
        assert UnitConverter.bits_to_bytes(8) == 1
        assert UnitConverter.bits_to_bytes(0) == 0
        assert UnitConverter.bits_to_bytes(16) == 2

    def test_bytes_to_kilobytes(self):
        """Test bytes to kilobytes conversion."""
        assert UnitConverter.bytes_to_kilobytes(1024) == 1
        assert UnitConverter.bytes_to_kilobytes(0) == 0
        assert UnitConverter.bytes_to_kilobytes(2048) == 2

    def test_kilobytes_to_megabytes(self):
        """Test kilobytes to megabytes conversion."""
        assert UnitConverter.kilobytes_to_megabytes(1024) == 1
        assert UnitConverter.kilobytes_to_megabytes(0) == 0
        assert UnitConverter.kilobytes_to_megabytes(2048) == 2

    # Pressure conversions
    def test_pascal_to_bar(self):
        """Test pascal to bar conversion."""
        assert UnitConverter.pascal_to_bar(100000) == 1
        assert UnitConverter.pascal_to_bar(0) == 0
        assert UnitConverter.pascal_to_bar(200000) == 2

    def test_bar_to_atm(self):
        """Test bar to atmosphere conversion."""
        assert UnitConverter.bar_to_atm(1.01325) == pytest.approx(1)
        assert UnitConverter.bar_to_atm(0) == 0
        assert UnitConverter.bar_to_atm(2.0265) == pytest.approx(2)

    # Power conversions
    def test_watts_to_kilowatts(self):
        """Test watts to kilowatts conversion."""
        assert UnitConverter.watts_to_kilowatts(1000) == 1
        assert UnitConverter.watts_to_kilowatts(0) == 0
        assert UnitConverter.watts_to_kilowatts(2500) == 2.5

    def test_kilowatts_to_horsepower(self):
        """Test kilowatts to horsepower conversion."""
        assert UnitConverter.kilowatts_to_horsepower(1) == pytest.approx(1.34102)
        assert UnitConverter.kilowatts_to_horsepower(0) == 0
        assert UnitConverter.kilowatts_to_horsepower(10) == pytest.approx(13.4102)

    # Energy conversions
    def test_joules_to_calories(self):
        """Test joules to calories conversion."""
        assert UnitConverter.joules_to_calories(4.184) == pytest.approx(1)
        assert UnitConverter.joules_to_calories(0) == 0
        assert UnitConverter.joules_to_calories(8.368) == pytest.approx(2)

    def test_calories_to_kilowatt_hours(self):
        """Test calories to kilowatt hours conversion."""
        result = UnitConverter.calories_to_kilowatt_hours(1000000)
        assert result == pytest.approx(1.16222, rel=1e-3)
        assert UnitConverter.calories_to_kilowatt_hours(0) == 0

    # Frequency conversions
    def test_hertz_to_kilohertz(self):
        """Test hertz to kilohertz conversion."""
        assert UnitConverter.hertz_to_kilohertz(1000) == 1
        assert UnitConverter.hertz_to_kilohertz(0) == 0
        assert UnitConverter.hertz_to_kilohertz(2500) == 2.5

    def test_kilohertz_to_megahertz(self):
        """Test kilohertz to megahertz conversion."""
        assert UnitConverter.kilohertz_to_megahertz(1000) == 1
        assert UnitConverter.kilohertz_to_megahertz(0) == 0
        assert UnitConverter.kilohertz_to_megahertz(2500) == 2.5

    # Fuel economy conversions
    def test_km_per_liter_to_mpg(self):
        """Test kilometers per liter to miles per gallon conversion."""
        assert UnitConverter.km_per_liter_to_mpg(1) == pytest.approx(2.35215)
        assert UnitConverter.km_per_liter_to_mpg(0) == 0
        assert UnitConverter.km_per_liter_to_mpg(10) == pytest.approx(23.5215)

    def test_mpg_to_km_per_liter(self):
        """Test miles per gallon to kilometers per liter conversion."""
        assert UnitConverter.mpg_to_km_per_liter(2.35215) == pytest.approx(1)
        assert UnitConverter.mpg_to_km_per_liter(0) == 0
        assert UnitConverter.mpg_to_km_per_liter(30) == pytest.approx(12.756, rel=1e-3)

    # Electrical conversions
    def test_ampere_to_milliampere(self):
        """Test ampere to milliampere conversion."""
        assert UnitConverter.ampere_to_milliampere(1) == 1000
        assert UnitConverter.ampere_to_milliampere(0) == 0
        assert UnitConverter.ampere_to_milliampere(0.5) == 500

    def test_volt_to_kilovolt(self):
        """Test volt to kilovolt conversion."""
        assert UnitConverter.volt_to_kilovolt(1000) == 1
        assert UnitConverter.volt_to_kilovolt(0) == 0
        assert UnitConverter.volt_to_kilovolt(2500) == 2.5

    def test_ohm_to_kiloohm(self):
        """Test ohm to kiloohm conversion."""
        assert UnitConverter.ohm_to_kiloohm(1000) == 1
        assert UnitConverter.ohm_to_kiloohm(0) == 0
        assert UnitConverter.ohm_to_kiloohm(2500) == 2.5

    # Magnetic conversions
    def test_weber_to_tesla(self):
        """Test weber to tesla conversion."""
        assert UnitConverter.weber_to_tesla(1, 1) == 1
        assert UnitConverter.weber_to_tesla(2, 2) == 1
        assert UnitConverter.weber_to_tesla(10, 5) == 2
        assert UnitConverter.weber_to_tesla(1) == 1  # Default area = 1

    def test_gauss_to_tesla(self):
        """Test gauss to tesla conversion."""
        assert UnitConverter.gauss_to_tesla(10000) == 1
        assert UnitConverter.gauss_to_tesla(0) == 0
        assert UnitConverter.gauss_to_tesla(5000) == 0.5

    def test_tesla_to_weber(self):
        """Test tesla to weber conversion."""
        assert UnitConverter.tesla_to_weber(1, 1) == 1
        assert UnitConverter.tesla_to_weber(1, 2) == 2
        assert UnitConverter.tesla_to_weber(2, 5) == 10
        assert UnitConverter.tesla_to_weber(1) == 1  # Default area = 1

    def test_tesla_to_gauss(self):
        """Test tesla to gauss conversion."""
        assert UnitConverter.tesla_to_gauss(1) == 10000
        assert UnitConverter.tesla_to_gauss(0) == 0
        assert UnitConverter.tesla_to_gauss(0.5) == 5000

    # Radiation conversions
    def test_gray_to_sievert(self):
        """Test gray to sievert conversion."""
        assert UnitConverter.gray_to_sievert(1) == 1
        assert UnitConverter.gray_to_sievert(0) == 0
        assert UnitConverter.gray_to_sievert(5) == 5

    # Light intensity conversions
    def test_lux_to_lumen(self):
        """Test lux to lumen conversion."""
        assert UnitConverter.lux_to_lumen(100, 2) == 200
        assert UnitConverter.lux_to_lumen(0, 5) == 0
        assert UnitConverter.lux_to_lumen(50, 1) == 50

    def test_lumen_to_lux(self):
        """Test lumen to lux conversion."""
        assert UnitConverter.lumen_to_lux(200, 2) == 100
        assert UnitConverter.lumen_to_lux(0, 5) == 0
        assert UnitConverter.lumen_to_lux(50, 1) == 50

    # Test round-trip conversions to ensure consistency
    def test_temperature_round_trip(self):
        """Test round-trip temperature conversions."""
        celsius = 25
        fahrenheit = UnitConverter.celsius_to_fahrenheit(celsius)
        back_to_celsius = UnitConverter.fahrenheit_to_celsius(fahrenheit)
        assert back_to_celsius == pytest.approx(celsius)

    def test_length_round_trip(self):
        """Test round-trip length conversions."""
        meters = 10
        feet = UnitConverter.meters_to_feet(meters)
        back_to_meters = UnitConverter.feet_to_meters(feet)
        assert back_to_meters == pytest.approx(meters)

    def test_weight_round_trip(self):
        """Test round-trip weight conversions."""
        kg = 5
        lbs = UnitConverter.kilograms_to_pounds(kg)
        back_to_kg = UnitConverter.pounds_to_kilograms(lbs)
        assert back_to_kg == pytest.approx(kg)

    def test_time_round_trip(self):
        """Test round-trip time conversions."""
        minutes = 30
        seconds = UnitConverter.minutes_to_seconds(minutes)
        back_to_minutes = UnitConverter.seconds_to_minutes(seconds)
        assert back_to_minutes == pytest.approx(minutes)