# Unit Converter Tools

The unit converter tools provide conversion functions between various units, including length, mass, temperature, time, etc.

## Class Overview

The unit converter tools mainly include the following classes:

- `UnitConverter` - A class that provides various unit conversion functions

## Usage

### Basic Usage

```python
from toolregistry_hub import UnitConverter

# Length conversion
meters = UnitConverter.feet_to_meters(10)
print(f"10 feet = {meters} meters")

# Temperature conversion
celsius = UnitConverter.fahrenheit_to_celsius(98.6)
print(f"98.6 Fahrenheit = {celsius} Celsius")

# Mass conversion
kilograms = UnitConverter.pounds_to_kilograms(150)
print(f"150 pounds = {kilograms} kilograms")
```

## Detailed API

### UnitConverter Class

`UnitConverter` is a class that provides various unit conversion functions.

#### Length Conversion Methods

- `meters_to_feet(meters: float) -> float`: Convert meters to feet
- `feet_to_meters(feet: float) -> float`: Convert feet to meters
- `kilometers_to_miles(kilometers: float) -> float`: Convert kilometers to miles
- `miles_to_kilometers(miles: float) -> float`: Convert miles to kilometers
- `inches_to_centimeters(inches: float) -> float`: Convert inches to centimeters
- `centimeters_to_inches(centimeters: float) -> float`: Convert centimeters to inches
- `meters_to_yards(meters: float) -> float`: Convert meters to yards
- `yards_to_meters(yards: float) -> float`: Convert yards to meters

#### Mass Conversion Methods

- `kilograms_to_pounds(kilograms: float) -> float`: Convert kilograms to pounds
- `pounds_to_kilograms(pounds: float) -> float`: Convert pounds to kilograms
- `grams_to_ounces(grams: float) -> float`: Convert grams to ounces
- `ounces_to_grams(ounces: float) -> float`: Convert ounces to grams
- `kilograms_to_stones(kilograms: float) -> float`: Convert kilograms to stones
- `stones_to_kilograms(stones: float) -> float`: Convert stones to kilograms

#### Temperature Conversion Methods

- `celsius_to_fahrenheit(celsius: float) -> float`: Convert Celsius to Fahrenheit
- `fahrenheit_to_celsius(fahrenheit: float) -> float`: Convert Fahrenheit to Celsius
- `celsius_to_kelvin(celsius: float) -> float`: Convert Celsius to Kelvin
- `kelvin_to_celsius(kelvin: float) -> float`: Convert Kelvin to Celsius
- `fahrenheit_to_kelvin(fahrenheit: float) -> float`: Convert Fahrenheit to Kelvin
- `kelvin_to_fahrenheit(kelvin: float) -> float`: Convert Kelvin to Fahrenheit

#### Volume Conversion Methods

- `liters_to_gallons(liters: float) -> float`: Convert liters to gallons
- `gallons_to_liters(gallons: float) -> float`: Convert gallons to liters
- `cubic_meters_to_cubic_feet(cubic_meters: float) -> float`: Convert cubic meters to cubic feet
- `cubic_feet_to_cubic_meters(cubic_feet: float) -> float`: Convert cubic feet to cubic meters
- `milliliters_to_fluid_ounces(milliliters: float) -> float`: Convert milliliters to fluid ounces
- `fluid_ounces_to_milliliters(fluid_ounces: float) -> float`: Convert fluid ounces to milliliters

#### Area Conversion Methods

- `square_meters_to_square_feet(square_meters: float) -> float`: Convert square meters to square feet
- `square_feet_to_square_meters(square_feet: float) -> float`: Convert square feet to square meters
- `hectares_to_acres(hectares: float) -> float`: Convert hectares to acres
- `acres_to_hectares(acres: float) -> float`: Convert acres to hectares

#### Speed Conversion Methods

- `kilometers_per_hour_to_miles_per_hour(kph: float) -> float`: Convert kilometers/hour to miles/hour
- `miles_per_hour_to_kilometers_per_hour(mph: float) -> float`: Convert miles/hour to kilometers/hour
- `meters_per_second_to_feet_per_second(mps: float) -> float`: Convert meters/second to feet/second
- `feet_per_second_to_meters_per_second(fps: float) -> float`: Convert feet/second to meters/second

#### Energy Conversion Methods

- `joules_to_calories(joules: float) -> float`: Convert joules to calories
- `calories_to_joules(calories: float) -> float`: Convert calories to joules
- `kilowatt_hours_to_megajoules(kwh: float) -> float`: Convert kilowatt hours to megajoules
- `megajoules_to_kilowatt_hours(mj: float) -> float`: Convert megajoules to kilowatt hours

#### Pressure Conversion Methods

- `pascals_to_psi(pascals: float) -> float`: Convert pascals to pounds per square inch
- `psi_to_pascals(psi: float) -> float`: Convert pounds per square inch to pascals
- `bars_to_atmospheres(bars: float) -> float`: Convert bars to atmospheres
- `atmospheres_to_bars(atmospheres: float) -> float`: Convert atmospheres to bars

#### Electromagnetic Unit Conversion Methods

- `weber_to_tesla(weber: float, area: float = 1.0) -> float`: Convert weber to tesla
- `tesla_to_weber(tesla: float, area: float = 1.0) -> float`: Convert tesla to weber

## Examples

### Length Conversion

```python
from toolregistry_hub import UnitConverter

# Feet to meters
meters = UnitConverter.feet_to_meters(10)
print(f"10 feet = {meters} meters")

# Miles to kilometers
kilometers = UnitConverter.miles_to_kilometers(5)
print(f"5 miles = {kilometers} kilometers")

# Centimeters to inches
inches = UnitConverter.centimeters_to_inches(30)
print(f"30 centimeters = {inches} inches")
```

### Mass Conversion

```python
from toolregistry_hub import UnitConverter

# Kilograms to pounds
pounds = UnitConverter.kilograms_to_pounds(70)
print(f"70 kilograms = {pounds} pounds")

# Ounces to grams
grams = UnitConverter.ounces_to_grams(16)
print(f"16 ounces = {grams} grams")

# Stones to kilograms
kilograms = UnitConverter.stones_to_kilograms(10)
print(f"10 stones = {kilograms} kilograms")
```

### Temperature Conversion

```python
from toolregistry_hub import UnitConverter

# Celsius to Fahrenheit
fahrenheit = UnitConverter.celsius_to_fahrenheit(25)
print(f"25 Celsius = {fahrenheit} Fahrenheit")

# Fahrenheit to Celsius
celsius = UnitConverter.fahrenheit_to_celsius(98.6)
print(f"98.6 Fahrenheit = {celsius} Celsius")

# Celsius to Kelvin
kelvin = UnitConverter.celsius_to_kelvin(0)
print(f"0 Celsius = {kelvin} Kelvin")
```

### Volume Conversion

```python
from toolregistry_hub import UnitConverter

# Liters to gallons
gallons = UnitConverter.liters_to_gallons(10)
print(f"10 liters = {gallons} gallons")

# Cubic meters to cubic feet
cubic_feet = UnitConverter.cubic_meters_to_cubic_feet(2)
print(f"2 cubic meters = {cubic_feet} cubic feet")

# Fluid ounces to milliliters
milliliters = UnitConverter.fluid_ounces_to_milliliters(8)
print(f"8 fluid ounces = {milliliters} milliliters")
```

## Navigation

- [Back to Home](../readme_en.md)
- [View Navigation Page](navigation.md)
- [Calculator Tools](calculator.md)
- [Date Time Tools](datetime.md)
- [File Operations Tools](file_ops.md)
- [File System Tools](filesystem.md)
- [Web Search Tools](websearch/index.md)
- [Other Tools](other_tools.md)
