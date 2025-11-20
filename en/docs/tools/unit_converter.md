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

# Length conversion
feet = UnitConverter.meters_to_feet(2.5)
print(f"2.5 meters = {feet:.2f} feet")

# Weight conversion
pounds = UnitConverter.kilograms_to_pounds(70)
print(f"70 kg = {pounds:.1f} lbs")
```

## 📋 Conversion Categories

### Temperature Conversions

| From → To            | Method                    | Example                                          |
| -------------------- | ------------------------- | ------------------------------------------------ |
| Celsius → Fahrenheit | `celsius_to_fahrenheit()` | `UnitConverter.celsius_to_fahrenheit(25)` = 77.0 |
| Fahrenheit → Celsius | `fahrenheit_to_celsius()` | `UnitConverter.fahrenheit_to_celsius(77)` = 25.0 |
| Kelvin → Celsius     | `kelvin_to_celsius()`     | `UnitConverter.kelvin_to_celsius(298.15)` = 25.0 |
| Celsius → Kelvin     | `celsius_to_kelvin()`     | `UnitConverter.celsius_to_kelvin(25)` = 298.15   |

### Length Conversions

| From → To            | Method                    | Example                                            |
| -------------------- | ------------------------- | -------------------------------------------------- |
| Meters → Feet        | `meters_to_feet()`        | `UnitConverter.meters_to_feet(1)` = 3.28084        |
| Feet → Meters        | `feet_to_meters()`        | `UnitConverter.feet_to_meters(10)` = 3.048         |
| Centimeters → Inches | `centimeters_to_inches()` | `UnitConverter.centimeters_to_inches(25.4)` = 10.0 |
| Inches → Centimeters | `inches_to_centimeters()` | `UnitConverter.inches_to_centimeters(12)` = 30.48  |

### Weight Conversions

| From → To          | Method                  | Example                                           |
| ------------------ | ----------------------- | ------------------------------------------------- |
| Kilograms → Pounds | `kilograms_to_pounds()` | `UnitConverter.kilograms_to_pounds(1)` = 2.20462  |
| Pounds → Kilograms | `pounds_to_kilograms()` | `UnitConverter.pounds_to_kilograms(10)` = 4.53592 |

### Time Conversions

| From → To         | Method                 | Example                                         |
| ----------------- | ---------------------- | ----------------------------------------------- |
| Seconds → Minutes | `seconds_to_minutes()` | `UnitConverter.seconds_to_minutes(180)` = 3.0   |
| Minutes → Seconds | `minutes_to_seconds()` | `UnitConverter.minutes_to_seconds(2.5)` = 150.0 |

### Capacity Conversions

| From → To        | Method                | Example                                         |
| ---------------- | --------------------- | ----------------------------------------------- |
| Liters → Gallons | `liters_to_gallons()` | `UnitConverter.liters_to_gallons(10)` = 2.64172 |
| Gallons → Liters | `gallons_to_liters()` | `UnitConverter.gallons_to_liters(1)` = 3.78541  |

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

# Liquid measurements
ml_in_cup = 240
cups = 2.5
ml = cups * ml_in_cup
print(f"{cups} cups = {ml} ml")

# Weight conversions
pounds = 1.5  # 1.5 lbs of meat
kg = UnitConverter.pounds_to_kilograms(pounds)
print(f"{pounds} lbs = {kg:.3f} kg")
```

### Travel Conversions

```python
from toolregistry_hub import UnitConverter

# Distance conversions
kmh = 100  # Speed limit in km/h
mph = UnitConverter.kmh_to_mph(kmh)
print(f"Speed limit: {kmh} km/h = {mph:.1f} mph")

# Fuel efficiency
km_per_l = 12  # 12 km/L fuel efficiency
mpg = UnitConverter.km_per_liter_to_mpg(km_per_l)
print(f"Fuel efficiency: {km_per_l} km/L = {mpg:.1f} mpg")

# Temperature conversion
weather_c = 22  # Weather in Celsius
weather_f = UnitConverter.celsius_to_fahrenheit(weather_c)
print(f"Weather: {weather_c}°C = {weather_f}°F")
```

### Scientific Calculations

```python
from toolregistry_hub import UnitConverter

# Electrical calculations
voltage_kv = 132  # High voltage line
voltage_v = UnitConverter.kilovolt_to_volt(voltage_kv)
print(f"Voltage: {voltage_kv} kV = {voltage_v} V")

# Data storage
bytes_data = 1024 * 1024 * 500  # 500 MB in bytes
mb_data = UnitConverter.bytes_to_megabytes(bytes_data)
print(f"Data size: {bytes_data} bytes = {mb_data} MB")

# Pressure conversions
pressure_bar = 2.5  # Pressure in bar
pressure_atm = UnitConverter.bar_to_atm(pressure_bar)
print(f"Pressure: {pressure_bar} bar = {pressure_atm:.2f} atm")
```

### Engineering Conversions

```python
from toolregistry_hub import UnitConverter

# Material dimensions
length_ft = 10.5  # Length in feet
length_m = UnitConverter.feet_to_meters(length_ft)
print(f"Length: {length_ft} ft = {length_m:.3f} m")

# Area calculations
area_sqm = 150  # Area in square meters
area_sqft = UnitConverter.square_meters_to_square_feet(area_sqm)
print(f"Area: {area_sqm} m² = {area_sqft:.1f} ft²")

# Power calculations
horsepower = 250  # Engine power in HP
kilowatts = UnitConverter.horsepower_to_kilowatts(horsepower)
print(f"Power: {horsepower} HP = {kilowatts:.1f} kW")
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
