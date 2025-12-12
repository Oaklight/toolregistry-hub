---
title: Unit Converter Tools
summary: Comprehensive unit conversion functions for various measurement systems
description: Complete unit conversion tools supporting temperature, length, weight, time, capacity, area, speed, data storage, pressure, power, energy, and more measurement types.
keywords: unit converter, measurement conversion, temperature, length, weight, time, data conversion
author: Oaklight
---

# Unit Converter Tools

The UnitConverter tools provide comprehensive unit conversion functions for various measurement systems. These tools support conversions across multiple categories including temperature, length, weight, time, capacity, area, speed, data storage, pressure, power, energy, and many more.

!!! note "API Change Notice (v0.5.2+)"
    Starting from v0.5.2, the UnitConverter API has undergone a major change. Direct method calls (like `celsius_to_fahrenheit()`) are no longer exposed. Instead, use the unified `convert()` method. This reduces LLM tool field length and improves performance.
    
    **Old usage** (v0.5.1 and earlier):
    ```python
    result = UnitConverter.celsius_to_fahrenheit(25)
    ```
    
    **New usage** (v0.5.2+):
    ```python
    result = UnitConverter.convert(25, "celsius_to_fahrenheit")
    ```
    
    All conversion functionality remains the same, only the calling pattern has changed.

## 🎯 Overview

The UnitConverter class offers precise conversions between different units of measurement:

- **Temperature**: Celsius, Fahrenheit, Kelvin
- **Length**: Meters, feet, inches, centimeters
- **Weight**: Kilograms, pounds
- **Time**: Seconds, minutes, hours
- **Capacity**: Liters, gallons
- **Area**: Square meters, square feet
- **Speed**: km/h, mph
- **Data Storage**: Bits, bytes, kilobytes, megabytes
- **Pressure**: Pascal, bar, atmosphere
- **Power**: Watts, kilowatts, horsepower
- **Energy**: Joules, calories, kilowatt-hours
- **Frequency**: Hertz, kilohertz, megahertz
- **Fuel Economy**: km/L, mpg
- **Electrical**: Ampere, volt, ohm
- **Magnetic**: Weber, tesla, gauss
- **Radiation**: Gray, sievert
- **Light Intensity**: Lux, lumen

## 🚀 Quick Start

```python
from toolregistry_hub import UnitConverter

# Temperature conversion
celsius = UnitConverter.convert(98.6, "fahrenheit_to_celsius")
print(f"98.6°F = {celsius:.1f}°C")
# Output: 98.6°F = 37.0°C

# Length conversion
feet = UnitConverter.convert(2.5, "meters_to_feet")
print(f"2.5 meters = {feet:.2f} feet")
# Output: 2.5 meters = 8.20 feet

# Weight conversion
pounds = UnitConverter.convert(70, "kilograms_to_pounds")
print(f"70 kg = {pounds:.1f} lbs")
# Output: 70 kg = 154.3 lbs

# List all available conversions
import json
conversions = json.loads(UnitConverter.list_conversions("all"))
print(f"Available conversions: {len(conversions)}")

# List conversions by category
temp_conversions = json.loads(UnitConverter.list_conversions("temperature"))
print(f"Temperature conversions: {temp_conversions}")

# Get help for a specific conversion
help_text = UnitConverter.help("celsius_to_fahrenheit")
print(help_text)
```

## 📋 Conversion Categories

### Temperature Conversions

| From → To            | Conversion Function     | Formula/Conversion Factor | Example                                                     |
| -------------------- | ----------------------- | ------------------------- | ----------------------------------------------------------- |
| Celsius → Fahrenheit | `celsius_to_fahrenheit` | °F = (°C × 9/5) + 32      | `UnitConverter.convert(25, "celsius_to_fahrenheit") = 77.0` |
| Fahrenheit → Celsius | `fahrenheit_to_celsius` | °C = (°F - 32) × 5/9      | `UnitConverter.convert(77, "fahrenheit_to_celsius") = 25.0` |
| Kelvin → Celsius     | `kelvin_to_celsius`     | °C = K - 273.15           | `UnitConverter.convert(298.15, "kelvin_to_celsius") = 25.0` |
| Celsius → Kelvin     | `celsius_to_kelvin`     | K = °C + 273.15           | `UnitConverter.convert(25, "celsius_to_kelvin") = 298.15`   |

### Length Conversions

| From → To            | Method                    | Conversion Factor      | Example                                            |
| -------------------- | ------------------------- | ---------------------- | -------------------------------------------------- |
| Meters → Feet        | `meters_to_feet()`        | 1 meter = 3.28084 feet | `UnitConverter.meters_to_feet(1) = 3.28084`        |
| Feet → Meters        | `feet_to_meters()`        | 1 foot = 0.3048 meters | `UnitConverter.feet_to_meters(10) = 3.048`         |
| Centimeters → Inches | `centimeters_to_inches()` | 1 cm = 0.393701 inches | `UnitConverter.centimeters_to_inches(25.4) = 10.0` |
| Inches → Centimeters | `inches_to_centimeters()` | 1 inch = 2.54 cm       | `UnitConverter.inches_to_centimeters(12) = 30.48`  |

### Weight Conversions

| From → To          | Method                  | Conversion Factor  | Example                                           |
| ------------------ | ----------------------- | ------------------ | ------------------------------------------------- |
| Kilograms → Pounds | `kilograms_to_pounds()` | 1 kg = 2.20462 lbs | `UnitConverter.kilograms_to_pounds(1) = 2.20462`  |
| Pounds → Kilograms | `pounds_to_kilograms()` | 1 lb = 0.453592 kg | `UnitConverter.pounds_to_kilograms(10) = 4.53592` |

### Time Conversions

| From → To         | Method                 | Conversion Factor     | Example                                         |
| ----------------- | ---------------------- | --------------------- | ----------------------------------------------- |
| Seconds → Minutes | `seconds_to_minutes()` | 1 minute = 60 seconds | `UnitConverter.seconds_to_minutes(180) = 3.0`   |
| Minutes → Seconds | `minutes_to_seconds()` | 1 minute = 60 seconds | `UnitConverter.minutes_to_seconds(2.5) = 150.0` |

### Capacity Conversions

| From → To        | Method                | Conversion Factor         | Example                                         |
| ---------------- | --------------------- | ------------------------- | ----------------------------------------------- |
| Liters → Gallons | `liters_to_gallons()` | 1 gallon = 3.78541 liters | `UnitConverter.liters_to_gallons(10) = 2.64172` |
| Gallons → Liters | `gallons_to_liters()` | 1 gallon = 3.78541 liters | `UnitConverter.gallons_to_liters(1) = 3.78541`  |

### Area Conversions

| From → To                   | Method                           | Conversion Factor   | Example                                                    |
| --------------------------- | -------------------------------- | ------------------- | ---------------------------------------------------------- |
| Square Meters → Square Feet | `square_meters_to_square_feet()` | 1 m² = 10.7639 ft²  | `UnitConverter.square_meters_to_square_feet(1) = 10.7639`  |
| Square Feet → Square Meters | `square_feet_to_square_meters()` | 1 ft² = 0.092903 m² | `UnitConverter.square_feet_to_square_meters(10) = 0.92903` |

### Speed Conversions

| From → To  | Method         | Conversion Factor    | Example                                   |
| ---------- | -------------- | -------------------- | ----------------------------------------- |
| km/h → mph | `kmh_to_mph()` | 1 mph = 1.60934 km/h | `UnitConverter.kmh_to_mph(100) = 62.1371` |
| mph → km/h | `mph_to_kmh()` | 1 mph = 1.60934 km/h | `UnitConverter.mph_to_kmh(60) = 96.5606`  |

### Data Storage Conversions

| From → To             | Method                     | Conversion Factor | Example                                            |
| --------------------- | -------------------------- | ----------------- | -------------------------------------------------- |
| Bits → Bytes          | `bits_to_bytes()`          | 1 byte = 8 bits   | `UnitConverter.bits_to_bytes(8) = 1.0`             |
| Bytes → Kilobytes     | `bytes_to_kilobytes()`     | 1 KB = 1024 bytes | `UnitConverter.bytes_to_kilobytes(1024) = 1.0`     |
| Kilobytes → Megabytes | `kilobytes_to_megabytes()` | 1 MB = 1024 KB    | `UnitConverter.kilobytes_to_megabytes(1024) = 1.0` |

### Pressure Conversions

| From → To        | Method            | Conversion Factor   | Example                                     |
| ---------------- | ----------------- | ------------------- | ------------------------------------------- |
| Pascal → Bar     | `pascal_to_bar()` | 1 bar = 100,000 Pa  | `UnitConverter.pascal_to_bar(100000) = 1.0` |
| Bar → Atmosphere | `bar_to_atm()`    | 1 atm = 1.01325 bar | `UnitConverter.bar_to_atm(1.01325) = 1.0`   |

### Power Conversions

| From → To              | Method                      | Conversion Factor | Example                                              |
| ---------------------- | --------------------------- | ----------------- | ---------------------------------------------------- |
| Watts → Kilowatts      | `watts_to_kilowatts()`      | 1 kW = 1000 W     | `UnitConverter.watts_to_kilowatts(1500) = 1.5`       |
| Kilowatts → Horsepower | `kilowatts_to_horsepower()` | 1 hp = 0.7457 kW  | `UnitConverter.kilowatts_to_horsepower(1) = 1.34102` |

### Energy Conversions

| From → To                 | Method                         | Conversion Factor   | Example                                                  |
| ------------------------- | ------------------------------ | ------------------- | -------------------------------------------------------- |
| Joules → Calories         | `joules_to_calories()`         | 1 cal = 4.184 J     | `UnitConverter.joules_to_calories(4184) = 1000.0`        |
| Calories → Kilowatt-hours | `calories_to_kilowatt_hours()` | 1 kWh = 860,421 cal | `UnitConverter.calories_to_kilowatt_hours(860421) = 1.0` |

### Frequency Conversions

| From → To             | Method                     | Conversion Factor | Example                                            |
| --------------------- | -------------------------- | ----------------- | -------------------------------------------------- |
| Hertz → Kilohertz     | `hertz_to_kilohertz()`     | 1 kHz = 1000 Hz   | `UnitConverter.hertz_to_kilohertz(1000) = 1.0`     |
| Kilohertz → Megahertz | `kilohertz_to_megahertz()` | 1 MHz = 1000 kHz  | `UnitConverter.kilohertz_to_megahertz(1000) = 1.0` |

### Fuel Economy Conversions

| From → To  | Method                  | Conversion Factor     | Example                                         |
| ---------- | ----------------------- | --------------------- | ----------------------------------------------- |
| km/L → mpg | `km_per_liter_to_mpg()` | 1 mpg = 0.425144 km/L | `UnitConverter.km_per_liter_to_mpg(12) = 28.24` |
| mpg → km/L | `mpg_to_km_per_liter()` | 1 mpg = 0.425144 km/L | `UnitConverter.mpg_to_km_per_liter(30) = 12.75` |

### Electrical Conversions

| From → To            | Method                    | Conversion Factor | Example                                           |
| -------------------- | ------------------------- | ----------------- | ------------------------------------------------- |
| Ampere → Milliampere | `ampere_to_milliampere()` | 1 A = 1000 mA     | `UnitConverter.ampere_to_milliampere(1) = 1000.0` |
| Volt → Kilovolt      | `volt_to_kilovolt()`      | 1 kV = 1000 V     | `UnitConverter.volt_to_kilovolt(1000) = 1.0`      |
| Ohm → Kiloohm        | `ohm_to_kiloohm()`        | 1 kΩ = 1000 Ω     | `UnitConverter.ohm_to_kiloohm(1000) = 1.0`        |

### Magnetic Conversions

| From → To     | Method             | Formula/Conversion Factor              | Example                                     |
| ------------- | ------------------ | -------------------------------------- | ------------------------------------------- |
| Weber → Tesla | `weber_to_tesla()` | B = Φ/A (A is area in square meters)   | `UnitConverter.weber_to_tesla(1, 1) = 1.0`  |
| Gauss → Tesla | `gauss_to_tesla()` | 1 T = 10,000 G                         | `UnitConverter.gauss_to_tesla(10000) = 1.0` |
| Tesla → Weber | `tesla_to_weber()` | Φ = B × A (A is area in square meters) | `UnitConverter.tesla_to_weber(1, 1) = 1.0`  |
| Tesla → Gauss | `tesla_to_gauss()` | 1 T = 10,000 G                         | `UnitConverter.tesla_to_gauss(1) = 10000.0` |

### Radiation Conversions

| From → To      | Method              | Note                                     | Example                                  |
| -------------- | ------------------- | ---------------------------------------- | ---------------------------------------- |
| Gray → Sievert | `gray_to_sievert()` | For most types of radiation, 1 Gy = 1 Sv | `UnitConverter.gray_to_sievert(1) = 1.0` |

### Light Intensity Conversions

| From → To   | Method           | Formula                             | Example                                      |
| ----------- | ---------------- | ----------------------------------- | -------------------------------------------- |
| Lux → Lumen | `lux_to_lumen()` | lumens = lux × area (square meters) | `UnitConverter.lux_to_lumen(100, 2) = 200.0` |
| Lumen → Lux | `lumen_to_lux()` | lux = lumens / area (square meters) | `UnitConverter.lumen_to_lux(200, 2) = 100.0` |

## 🛠️ Practical Examples

### Cooking Conversions

```python
from toolregistry_hub import UnitConverter

# Recipe conversions
oven_temp_f = 350  # 350°F for baking
oven_temp_c = UnitConverter.convert(oven_temp_f, "fahrenheit_to_celsius")
print(f"Preheat oven to {oven_temp_c:.0f}°C")
# Output: Preheat oven to 177°C

# Liquid measurements
ml_in_cup = 240
cups = 2.5
ml = cups * ml_in_cup
print(f"{cups} cups = {ml} ml")
# Output: 2.5 cups = 600.0 ml

# Weight conversions
pounds = 1.5  # 1.5 lbs of meat
kg = UnitConverter.convert(pounds, "pounds_to_kilograms")
print(f"{pounds} lbs = {kg:.3f} kg")
# Output: 1.5 lbs = 0.680 kg
```

### Travel Conversions

```python
from toolregistry_hub import UnitConverter

# Distance conversions
kmh = 100  # Speed limit in km/h
mph = UnitConverter.convert(kmh, "kmh_to_mph")
print(f"Speed limit: {kmh} km/h = {mph:.1f} mph")
# Output: Speed limit: 100 km/h = 62.1 mph

# Fuel efficiency
km_per_l = 12  # 12 km/L fuel efficiency
mpg = UnitConverter.convert(km_per_l, "km_per_liter_to_mpg")
print(f"Fuel efficiency: {km_per_l} km/L = {mpg:.1f} mpg")
# Output: Fuel efficiency: 12 km/L = 28.2 mpg

# Temperature conversion
weather_c = 22  # Weather in Celsius
weather_f = UnitConverter.convert(weather_c, "celsius_to_fahrenheit")
print(f"Weather: {weather_c}°C = {weather_f}°F")
# Output: Weather: 22°C = 71.6°F
```

### Scientific Calculations

```python
from toolregistry_hub import UnitConverter

# Electrical calculations
voltage_v = 132000  # High voltage line (volts)
voltage_kv = UnitConverter.convert(voltage_v, "volt_to_kilovolt")
print(f"Voltage: {voltage_v} V = {voltage_kv} kV")
# Output: Voltage: 132000 V = 132.0 kV

# Data storage
bytes_data = 1024 * 1024 * 500  # 500 MB in bytes
kb_data = UnitConverter.convert(bytes_data, "bytes_to_kilobytes")
mb_data = UnitConverter.convert(kb_data, "kilobytes_to_megabytes")
print(f"Data size: {bytes_data} bytes = {mb_data} MB")
# Output: Data size: 524288000 bytes = 500.0 MB

# Pressure conversions
pressure_bar = 2.5  # Pressure in bar
pressure_atm = UnitConverter.convert(pressure_bar, "bar_to_atm")
print(f"Pressure: {pressure_bar} bar = {pressure_atm:.2f} atm")
# Output: Pressure: 2.5 bar = 2.47 atm
```

### Engineering Conversions

```python
from toolregistry_hub import UnitConverter

# Material dimensions
length_ft = 10.5  # Length in feet
length_m = UnitConverter.convert(length_ft, "feet_to_meters")
print(f"Length: {length_ft} ft = {length_m:.3f} m")
# Output: Length: 10.5 ft = 3.200 m

# Area calculations
area_sqm = 150  # Area in square meters
area_sqft = UnitConverter.convert(area_sqm, "square_meters_to_square_feet")
print(f"Area: {area_sqm} m² = {area_sqft:.1f} ft²")
# Output: Area: 150 m² = 1614.6 ft²

# Power calculations
kilowatts = 186  # Engine power in kW
horsepower = UnitConverter.convert(kilowatts, "kilowatts_to_horsepower")
print(f"Power: {kilowatts} kW = {horsepower:.1f} HP")
# Output: Power: 186 kW = 249.4 HP

# Conversions with additional parameters (e.g., light intensity)
lux_value = 100
area = 2  # square meters
lumens = UnitConverter.convert(lux_value, "lux_to_lumen", area=area)
print(f"Luminous flux: {lux_value} lux × {area} m² = {lumens} lumens")
# Output: Luminous flux: 100 lux × 2 m² = 200.0 lumens
```

## 🚨 Important Notes

### Precision and Accuracy

- **Rounding**: Results may have small rounding errors due to floating-point arithmetic
- **Conversion factors**: Based on international standards
- **Temperature**: Kelvin uses 273.15 as the offset from Celsius

### Area and Volume

- **Area conversions**: Assume square units (m² to ft²)
- **Volume conversions**: Use liters and gallons for liquid measurements

### Magnetic Conversions

- **Area parameter**: Required for weber ↔ tesla conversions
- **Default area**: 1.0 square meter if not specified

### Data Storage

- **Binary system**: Uses 1024-based conversions (KiB, MiB, GiB)
- **Not decimal**: Different from SI prefixes (KB, MB, GB)

## 🔍 Conversion Tables

### Quick Reference

| Category        | Common Conversions                        |
| --------------- | ----------------------------------------- |
| **Temperature** | 0°C = 32°F = 273.15K                      |
| **Length**      | 1 inch = 2.54 cm, 1 mile = 1.609 km       |
| **Weight**      | 1 kg = 2.205 lbs, 1 oz = 28.35 g          |
| **Volume**      | 1 gallon = 3.785 L, 1 quart = 0.946 L     |
| **Speed**       | 100 km/h = 62.1 mph                       |
| **Area**        | 1 acre = 4047 m², 1 hectare = 2.471 acres |
