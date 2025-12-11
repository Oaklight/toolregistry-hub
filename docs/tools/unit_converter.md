---
title: Unit Converter Tools
summary: Comprehensive unit conversion functions for various measurement systems
description: Complete unit conversion tools supporting temperature, length, weight, time, capacity, area, speed, data storage, pressure, power, energy, and more measurement types.
keywords: unit converter, measurement conversion, temperature, length, weight, time, data conversion
author: Oaklight
---

# Unit Converter Tools

The UnitConverter tools provide comprehensive unit conversion functions for various measurement systems. These tools support conversions across multiple categories including temperature, length, weight, time, capacity, area, speed, data storage, pressure, power, energy, and many more.

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
celsius = UnitConverter.fahrenheit_to_celsius(98.6)
print(f"98.6°F = {celsius:.1f}°C")
# Output: 98.6°F = 37.0°C

# Length conversion
feet = UnitConverter.meters_to_feet(2.5)
print(f"2.5 meters = {feet:.2f} feet")
# Output: 2.5 meters = 8.20 feet

# Weight conversion
pounds = UnitConverter.kilograms_to_pounds(70)
print(f"70 kg = {pounds:.1f} lbs")
# Output: 70 kg = 154.3 lbs
```

## 📋 Conversion Categories

### Temperature Conversions

| From → To            | Method                    | Example                                          |
| -------------------- | ------------------------- | ------------------------------------------------ |
| Celsius → Fahrenheit | `celsius_to_fahrenheit()` | `UnitConverter.celsius_to_fahrenheit(25) = 77.0` |
| Fahrenheit → Celsius | `fahrenheit_to_celsius()` | `UnitConverter.fahrenheit_to_celsius(77) = 25.0` |
| Kelvin → Celsius     | `kelvin_to_celsius()`     | `UnitConverter.kelvin_to_celsius(298.15) = 25.0` |
| Celsius → Kelvin     | `celsius_to_kelvin()`     | `UnitConverter.celsius_to_kelvin(25) = 298.15`   |

### Length Conversions

| From → To            | Method                    | Example                                            |
| -------------------- | ------------------------- | -------------------------------------------------- |
| Meters → Feet        | `meters_to_feet()`        | `UnitConverter.meters_to_feet(1) = 3.28084`        |
| Feet → Meters        | `feet_to_meters()`        | `UnitConverter.feet_to_meters(10) = 3.048`         |
| Centimeters → Inches | `centimeters_to_inches()` | `UnitConverter.centimeters_to_inches(25.4) = 10.0` |
| Inches → Centimeters | `inches_to_centimeters()` | `UnitConverter.inches_to_centimeters(12) = 30.48`  |

### Weight Conversions

| From → To          | Method                  | Example                                           |
| ------------------ | ----------------------- | ------------------------------------------------- |
| Kilograms → Pounds | `kilograms_to_pounds()` | `UnitConverter.kilograms_to_pounds(1) = 2.20462`  |
| Pounds → Kilograms | `pounds_to_kilograms()` | `UnitConverter.pounds_to_kilograms(10) = 4.53592` |

### Time Conversions

| From → To         | Method                 | Example                                         |
| ----------------- | ---------------------- | ----------------------------------------------- |
| Seconds → Minutes | `seconds_to_minutes()` | `UnitConverter.seconds_to_minutes(180) = 3.0`   |
| Minutes → Seconds | `minutes_to_seconds()` | `UnitConverter.minutes_to_seconds(2.5) = 150.0` |

### Capacity Conversions

| From → To        | Method                | Example                                         |
| ---------------- | --------------------- | ----------------------------------------------- |
| Liters → Gallons | `liters_to_gallons()` | `UnitConverter.liters_to_gallons(10) = 2.64172` |
| Gallons → Liters | `gallons_to_liters()` | `UnitConverter.gallons_to_liters(1) = 3.78541`  |

### Area Conversions

| From → To                   | Method                           | Example                                                    |
| --------------------------- | -------------------------------- | ---------------------------------------------------------- |
| Square Meters → Square Feet | `square_meters_to_square_feet()` | `UnitConverter.square_meters_to_square_feet(1) = 10.7639`  |
| Square Feet → Square Meters | `square_feet_to_square_meters()` | `UnitConverter.square_feet_to_square_meters(10) = 0.92903` |

### Speed Conversions

| From → To  | Method         | Example                                   |
| ---------- | -------------- | ----------------------------------------- |
| km/h → mph | `kmh_to_mph()` | `UnitConverter.kmh_to_mph(100) = 62.1371` |
| mph → km/h | `mph_to_kmh()` | `UnitConverter.mph_to_kmh(60) = 96.5606`  |

### Data Storage Conversions

| From → To             | Method                     | Example                                            |
| --------------------- | -------------------------- | -------------------------------------------------- |
| Bits → Bytes          | `bits_to_bytes()`          | `UnitConverter.bits_to_bytes(8) = 1.0`             |
| Bytes → Kilobytes     | `bytes_to_kilobytes()`     | `UnitConverter.bytes_to_kilobytes(1024) = 1.0`     |
| Kilobytes → Megabytes | `kilobytes_to_megabytes()` | `UnitConverter.kilobytes_to_megabytes(1024) = 1.0` |

### Pressure Conversions

| From → To        | Method            | Example                                     |
| ---------------- | ----------------- | ------------------------------------------- |
| Pascal → Bar     | `pascal_to_bar()` | `UnitConverter.pascal_to_bar(100000) = 1.0` |
| Bar → Atmosphere | `bar_to_atm()`    | `UnitConverter.bar_to_atm(1.01325) = 1.0`   |

### Power Conversions

| From → To              | Method                      | Example                                              |
| ---------------------- | --------------------------- | ---------------------------------------------------- |
| Watts → Kilowatts      | `watts_to_kilowatts()`      | `UnitConverter.watts_to_kilowatts(1500) = 1.5`       |
| Kilowatts → Horsepower | `kilowatts_to_horsepower()` | `UnitConverter.kilowatts_to_horsepower(1) = 1.34102` |

### Energy Conversions

| From → To                 | Method                         | Example                                                  |
| ------------------------- | ------------------------------ | -------------------------------------------------------- |
| Joules → Calories         | `joules_to_calories()`         | `UnitConverter.joules_to_calories(4184) = 1000.0`        |
| Calories → Kilowatt-hours | `calories_to_kilowatt_hours()` | `UnitConverter.calories_to_kilowatt_hours(860421) = 1.0` |

### Frequency Conversions

| From → To             | Method                     | Example                                            |
| --------------------- | -------------------------- | -------------------------------------------------- |
| Hertz → Kilohertz     | `hertz_to_kilohertz()`     | `UnitConverter.hertz_to_kilohertz(1000) = 1.0`     |
| Kilohertz → Megahertz | `kilohertz_to_megahertz()` | `UnitConverter.kilohertz_to_megahertz(1000) = 1.0` |

### Fuel Economy Conversions

| From → To  | Method                  | Example                                         |
| ---------- | ----------------------- | ----------------------------------------------- |
| km/L → mpg | `km_per_liter_to_mpg()` | `UnitConverter.km_per_liter_to_mpg(12) = 28.24` |
| mpg → km/L | `mpg_to_km_per_liter()` | `UnitConverter.mpg_to_km_per_liter(30) = 12.75` |

### Electrical Conversions

| From → To            | Method                    | Example                                           |
| -------------------- | ------------------------- | ------------------------------------------------- |
| Ampere → Milliampere | `ampere_to_milliampere()` | `UnitConverter.ampere_to_milliampere(1) = 1000.0` |
| Volt → Kilovolt      | `volt_to_kilovolt()`      | `UnitConverter.volt_to_kilovolt(1000) = 1.0`      |
| Ohm → Kiloohm        | `ohm_to_kiloohm()`        | `UnitConverter.ohm_to_kiloohm(1000) = 1.0`        |

### Magnetic Conversions

| From → To     | Method             | Example                                     |
| ------------- | ------------------ | ------------------------------------------- |
| Weber → Tesla | `weber_to_tesla()` | `UnitConverter.weber_to_tesla(1, 1) = 1.0`  |
| Gauss → Tesla | `gauss_to_tesla()` | `UnitConverter.gauss_to_tesla(10000) = 1.0` |
| Tesla → Weber | `tesla_to_weber()` | `UnitConverter.tesla_to_weber(1, 1) = 1.0`  |
| Tesla → Gauss | `tesla_to_gauss()` | `UnitConverter.tesla_to_gauss(1) = 10000.0` |

### Radiation Conversions

| From → To      | Method              | Example                                  |
| -------------- | ------------------- | ---------------------------------------- |
| Gray → Sievert | `gray_to_sievert()` | `UnitConverter.gray_to_sievert(1) = 1.0` |

### Light Intensity Conversions

| From → To   | Method           | Example                                      |
| ----------- | ---------------- | -------------------------------------------- |
| Lux → Lumen | `lux_to_lumen()` | `UnitConverter.lux_to_lumen(100, 2) = 200.0` |
| Lumen → Lux | `lumen_to_lux()` | `UnitConverter.lumen_to_lux(200, 2) = 100.0` |

## 🔧 Complete API Reference

### Temperature Methods

#### `celsius_to_fahrenheit(celsius: float) -> float`

Convert Celsius to Fahrenheit.

**Formula:** `°F = (°C × 9/5) + 32`

#### `fahrenheit_to_celsius(fahrenheit: float) -> float`

Convert Fahrenheit to Celsius.

**Formula:** `°C = (°F - 32) × 5/9`

#### `kelvin_to_celsius(kelvin: float) -> float`

Convert Kelvin to Celsius.

**Formula:** `°C = K - 273.15`

#### `celsius_to_kelvin(celsius: float) -> float`

Convert Celsius to Kelvin.

**Formula:** `K = °C + 273.15`

### Length Methods

#### `meters_to_feet(meters: float) -> float`

Convert meters to feet.

**Conversion factor:** 1 meter = 3.28084 feet

#### `feet_to_meters(feet: float) -> float`

Convert feet to meters.

**Conversion factor:** 1 foot = 0.3048 meters

#### `centimeters_to_inches(cm: float) -> float`

Convert centimeters to inches.

**Conversion factor:** 1 cm = 0.393701 inches

#### `inches_to_centimeters(inches: float) -> float`

Convert inches to centimeters.

**Conversion factor:** 1 inch = 2.54 cm

### Weight Methods

#### `kilograms_to_pounds(kg: float) -> float`

Convert kilograms to pounds.

**Conversion factor:** 1 kg = 2.20462 lbs

#### `pounds_to_kilograms(lbs: float) -> float`

Convert pounds to kilograms.

**Conversion factor:** 1 lb = 0.453592 kg

### Time Methods

#### `seconds_to_minutes(seconds: float) -> float`

Convert seconds to minutes.

**Conversion factor:** 1 minute = 60 seconds

#### `minutes_to_seconds(minutes: float) -> float`

Convert minutes to seconds.

**Conversion factor:** 1 minute = 60 seconds

### Capacity Methods

#### `liters_to_gallons(liters: float) -> float`

Convert liters to gallons.

**Conversion factor:** 1 gallon = 3.78541 liters

#### `gallons_to_liters(gallons: float) -> float`

Convert gallons to liters.

**Conversion factor:** 1 gallon = 3.78541 liters

### Area Methods

#### `square_meters_to_square_feet(sqm: float) -> float`

Convert square meters to square feet.

**Conversion factor:** 1 m² = 10.7639 ft²

#### `square_feet_to_square_meters(sqft: float) -> float`

Convert square feet to square meters.

**Conversion factor:** 1 ft² = 0.092903 m²

### Speed Methods

#### `kmh_to_mph(kmh: float) -> float`

Convert kilometers per hour to miles per hour.

**Conversion factor:** 1 mph = 1.60934 km/h

#### `mph_to_kmh(mph: float) -> float`

Convert miles per hour to kilometers per hour.

**Conversion factor:** 1 mph = 1.60934 km/h

### Data Storage Methods

#### `bits_to_bytes(bits: float) -> float`

Convert bits to bytes.

**Conversion factor:** 1 byte = 8 bits

#### `bytes_to_kilobytes(bytes: float) -> float`

Convert bytes to kilobytes.

**Conversion factor:** 1 KB = 1024 bytes

#### `kilobytes_to_megabytes(kb: float) -> float`

Convert kilobytes to megabytes.

**Conversion factor:** 1 MB = 1024 KB

### Pressure Methods

#### `pascal_to_bar(pascal: float) -> float`

Convert pascal to bar.

**Conversion factor:** 1 bar = 100,000 Pa

#### `bar_to_atm(bar: float) -> float`

Convert bar to atmosphere.

**Conversion factor:** 1 atm = 1.01325 bar

### Power Methods

#### `watts_to_kilowatts(watts: float) -> float`

Convert watts to kilowatts.

**Conversion factor:** 1 kW = 1000 W

#### `kilowatts_to_horsepower(kw: float) -> float`

Convert kilowatts to horsepower.

**Conversion factor:** 1 hp = 0.7457 kW

### Energy Methods

#### `joules_to_calories(joules: float) -> float`

Convert joules to calories.

**Conversion factor:** 1 cal = 4.184 J

#### `calories_to_kilowatt_hours(calories: float) -> float`

Convert calories to kilowatt-hours.

**Conversion factor:** 1 kWh = 860,421 cal

### Frequency Methods

#### `hertz_to_kilohertz(hz: float) -> float`

Convert hertz to kilohertz.

**Conversion factor:** 1 kHz = 1000 Hz

#### `kilohertz_to_megahertz(khz: float) -> float`

Convert kilohertz to megahertz.

**Conversion factor:** 1 MHz = 1000 kHz

### Fuel Economy Methods

#### `km_per_liter_to_mpg(kmpl: float) -> float`

Convert kilometers per liter to miles per gallon.

**Conversion factor:** 1 mpg = 0.425144 km/L

#### `mpg_to_km_per_liter(mpg: float) -> float`

Convert miles per gallon to kilometers per liter.

**Conversion factor:** 1 mpg = 0.425144 km/L

### Electrical Methods

#### `ampere_to_milliampere(ampere: float) -> float`

Convert ampere to milliampere.

**Conversion factor:** 1 A = 1000 mA

#### `volt_to_kilovolt(volt: float) -> float`

Convert volt to kilovolt.

**Conversion factor:** 1 kV = 1000 V

#### `ohm_to_kiloohm(ohm: float) -> float`

Convert ohm to kiloohm.

**Conversion factor:** 1 kΩ = 1000 Ω

### Magnetic Methods

#### `weber_to_tesla(weber: float, area: float = 1.0) -> float`

Convert magnetic flux (weber) to magnetic flux density (tesla).

**Formula:** `B = Φ/A` where A is area in square meters

#### `gauss_to_tesla(gauss: float) -> float`

Convert gauss to tesla.

**Conversion factor:** 1 T = 10,000 G

#### `tesla_to_weber(tesla: float, area: float = 1.0) -> float`

Convert magnetic flux density (tesla) to magnetic flux (weber).

**Formula:** `Φ = B × A` where A is area in square meters

#### `tesla_to_gauss(tesla: float) -> float`

Convert tesla to gauss.

**Conversion factor:** 1 T = 10,000 G

### Radiation Methods

#### `gray_to_sievert(gray: float) -> float`

Convert gray to sievert.

**Note:** For most types of radiation, 1 Gy = 1 Sv

### Light Intensity Methods

#### `lux_to_lumen(lux: float, area: float) -> float`

Convert lux to lumen given an area in square meters.

**Formula:** `lumens = lux × area`

#### `lumen_to_lux(lumen: float, area: float) -> float`

Convert lumen to lux given an area in square meters.

**Formula:** `lux = lumens / area`

## 🛠️ Practical Examples

### Cooking Conversions

```python
from toolregistry_hub import UnitConverter

# Recipe conversions
oven_temp_f = 350  # 350°F for baking
oven_temp_c = UnitConverter.fahrenheit_to_celsius(oven_temp_f)
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
kg = UnitConverter.pounds_to_kilograms(pounds)
print(f"{pounds} lbs = {kg:.3f} kg")
# Output: 1.5 lbs = 0.680 kg
```

### Travel Conversions

```python
from toolregistry_hub import UnitConverter

# Distance conversions
kmh = 100  # Speed limit in km/h
mph = UnitConverter.kmh_to_mph(kmh)
print(f"Speed limit: {kmh} km/h = {mph:.1f} mph")
# Output: Speed limit: 100 km/h = 62.1 mph

# Fuel efficiency
km_per_l = 12  # 12 km/L fuel efficiency
mpg = UnitConverter.km_per_liter_to_mpg(km_per_l)
print(f"Fuel efficiency: {km_per_l} km/L = {mpg:.1f} mpg")
# Output: Fuel efficiency: 12 km/L = 28.2 mpg

# Temperature conversion
weather_c = 22  # Weather in Celsius
weather_f = UnitConverter.celsius_to_fahrenheit(weather_c)
print(f"Weather: {weather_c}°C = {weather_f}°F")
# Output: Weather: 22°C = 71.6°F
```

### Scientific Calculations

```python
from toolregistry_hub import UnitConverter

# Electrical calculations
voltage_v = 132000  # High voltage line (volts)
voltage_kv = UnitConverter.volt_to_kilovolt(voltage_v)
print(f"Voltage: {voltage_v} V = {voltage_kv} kV")
# Output: Voltage: 132000 V = 132.0 kV

# Data storage
bytes_data = 1024 * 1024 * 500  # 500 MB in bytes
kb_data = UnitConverter.bytes_to_kilobytes(bytes_data)
mb_data = UnitConverter.kilobytes_to_megabytes(kb_data)
print(f"Data size: {bytes_data} bytes = {mb_data} MB")
# Output: Data size: 524288000 bytes = 500.0 MB

# Pressure conversions
pressure_bar = 2.5  # Pressure in bar
pressure_atm = UnitConverter.bar_to_atm(pressure_bar)
print(f"Pressure: {pressure_bar} bar = {pressure_atm:.2f} atm")
# Output: Pressure: 2.5 bar = 2.47 atm
```

### Engineering Conversions

```python
from toolregistry_hub import UnitConverter

# Material dimensions
length_ft = 10.5  # Length in feet
length_m = UnitConverter.feet_to_meters(length_ft)
print(f"Length: {length_ft} ft = {length_m:.3f} m")
# Output: Length: 10.5 ft = 3.200 m

# Area calculations
area_sqm = 150  # Area in square meters
area_sqft = UnitConverter.square_meters_to_square_feet(area_sqm)
print(f"Area: {area_sqm} m² = {area_sqft:.1f} ft²")
# Output: Area: 150 m² = 1614.6 ft²

# Power calculations
kilowatts = 186  # Engine power in kW
horsepower = UnitConverter.kilowatts_to_horsepower(kilowatts)
print(f"Power: {kilowatts} kW = {horsepower:.1f} HP")
# Output: Power: 186 kW = 249.4 HP
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
