# Date Time Tools

The date time tools provide functions for handling dates, times, and timezone conversions.

## Class Overview

The date time tools mainly include the following classes:

- `DateTime` - Provides date time operations and timezone conversion functions

## Usage

### Basic Usage

```python
from toolregistry_hub import DateTime

# Get current time
current_time = DateTime.now()
print(current_time)  # Output: 2025-10-13T07:12:32.841Z

# Get current time for specific timezone
beijing_time = DateTime.now("Asia/Shanghai")
print(beijing_time)  # Output: 2025-10-13T15:12:32.841+08:00

# Timezone conversion
converted_time = DateTime.convert_timezone(
    "2025-10-13T07:12:32.841Z",
    from_timezone="UTC",
    to_timezone="Asia/Shanghai"
)
print(converted_time)  # Output: 2025-10-13T15:12:32.841+08:00
```

## Detailed API

### DateTime Class

`DateTime` is a class that provides date time operations and timezone conversion functions.

#### Methods

- `_parse_timezone_offset(timezone_str: str) -> timezone`: Parse timezone offset string
- `_get_timezone_obj(tz_str: str)`: Get timezone object from IANA name or UTC/GMT offset
- `now(timezone_name: Optional[str] = None) -> str`: Get current time, optionally specifying timezone
- `convert_timezone(time_str: str, from_timezone: str, to_timezone: str, format_str: Optional[str] = None) -> str`: Convert time between timezones

## Examples

### Getting Current Time

```python
from toolregistry_hub import DateTime

# Get current UTC time
utc_time = DateTime.now()
print(f"UTC time: {utc_time}")

# Get Beijing time
beijing_time = DateTime.now("Asia/Shanghai")
print(f"Beijing time: {beijing_time}")

# Get New York time
ny_time = DateTime.now("America/New_York")
print(f"New York time: {ny_time}")
```

### Timezone Conversion

```python
from toolregistry_hub import DateTime

# Convert UTC time to Beijing time
beijing_time = DateTime.convert_timezone(
    "2025-10-13T07:12:32.841Z",
    from_timezone="UTC",
    to_timezone="Asia/Shanghai"
)
print(f"Beijing time: {beijing_time}")

# Convert Beijing time to New York time
ny_time = DateTime.convert_timezone(
    "2025-10-13T15:12:32.841+08:00",
    from_timezone="Asia/Shanghai",
    to_timezone="America/New_York"
)
print(f"New York time: {ny_time}")

# Use custom format
formatted_time = DateTime.convert_timezone(
    "2025-10-13T15:12:32.841+08:00",
    from_timezone="Asia/Shanghai",
    to_timezone="America/New_York",
    format_str="%Y-%m-%d %H:%M:%S %Z"
)
print(f"Formatted New York time: {formatted_time}")
```

### Supported Timezone Formats

The DateTime tool supports the following timezone formats:

1. IANA timezone names, such as "Asia/Shanghai", "America/New_York"
2. UTC/GMT offsets, such as "UTC+8", "GMT-5"

```python
from toolregistry_hub import DateTime

# Use IANA timezone name
beijing_time = DateTime.now("Asia/Shanghai")
print(f"Beijing time (IANA): {beijing_time}")

# Use UTC offset
beijing_time_offset = DateTime.now("UTC+8")
print(f"Beijing time (UTC offset): {beijing_time_offset}")
```
