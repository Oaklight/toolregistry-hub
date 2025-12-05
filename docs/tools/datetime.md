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
print(current_time)  # Output: 2025-12-05T16:11:06+00:00

# Get current time for specific timezone
beijing_time = DateTime.now("Asia/Shanghai")
print(beijing_time)  # Output: 2025-12-06T00:11:06+08:00

# Timezone conversion
converted_time = DateTime.convert_timezone(
    "07:12",
    "UTC",
    "Asia/Shanghai"
)
print(converted_time)  # Output: {
#   'source_time': '2025-12-05T07:12:00+00:00',
#   'target_time': '2025-12-05T15:12:00+08:00',
#   'time_difference': '+8.0h',
#   'source_timezone': 'UTC',
#   'target_timezone': 'Asia/Shanghai'
# }
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
print(f"UTC time: {utc_time}")  # Output: UTC time: 2025-12-05T16:11:06+00:00

# Get Beijing time
beijing_time = DateTime.now("Asia/Shanghai")
print(f"Beijing time: {beijing_time}")  # Output: Beijing time: 2025-12-06T00:11:06+08:00

# Get New York time
ny_time = DateTime.now("America/New_York")
print(f"New York time: {ny_time}")  # Output: New York time: 2025-12-05T11:11:06-05:00
```

### Timezone Conversion

```python
from toolregistry_hub import DateTime

# Convert UTC time to Beijing time
beijing_time = DateTime.convert_timezone(
    "07:12",
    "UTC",
    "Asia/Shanghai"
)
print(f"Beijing time: {beijing_time}")  # Output: {
#   'source_time': '2025-12-05T07:12:00+00:00',
#   'target_time': '2025-12-05T15:12:00+08:00',
#   'time_difference': '+8.0h',
#   'source_timezone': 'UTC',
#   'target_timezone': 'Asia/Shanghai'
# }

# Convert Beijing time to New York time
ny_time = DateTime.convert_timezone(
    "15:12",
    "Asia/Shanghai",
    "America/New_York"
)
print(f"New York time: {ny_time}")  # Output: {
#   'source_time': '2025-12-06T15:12:00+08:00',
#   'target_time': '2025-12-06T02:12:00-05:00',
#   'time_difference': '-13.0h',
#   'source_timezone': 'Asia/Shanghai',
#   'target_timezone': 'America/New_York'
# }

# Use custom format
formatted_time = DateTime.convert_timezone(
    "15:12",
    "Asia/Shanghai",
    "America/New_York"
)
print(f"Formatted New York time: {formatted_time}")  # Output: {
#   'source_time': '2025-12-06T15:12:00+08:00',
#   'target_time': '2025-12-06T02:12:00-05:00',
#   'time_difference': '-13.0h',
#   'source_timezone': 'Asia/Shanghai',
#   'target_timezone': 'America/New_York'
# }
```

### Supported Timezone Formats

The DateTime tool supports the following timezone formats:

1. IANA timezone names, such as "Asia/Shanghai", "America/New_York"
2. UTC/GMT offsets, such as "UTC+8", "GMT-5"

```python
from toolregistry_hub import DateTime

# Use IANA timezone name
beijing_time = DateTime.now("Asia/Shanghai")
print(f"Beijing time (IANA): {beijing_time}")  # Output: Beijing time (IANA): 2025-12-06T00:11:06+08:00

# Use UTC offset
beijing_time_offset = DateTime.now("UTC+8")
print(f"Beijing time (UTC offset): {beijing_time_offset}")  # Output: Beijing time (UTC offset): 2025-12-06T00:11:06+08:00
```
