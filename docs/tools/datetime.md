# 日期时间工具

日期时间工具提供处理日期、时间和时区转换的功能。

## 类概述

日期时间工具主要包括以下类：

- `DateTime` - 提供日期时间操作和时区转换功能

## 使用

### 基本用法

```python
from toolregistry_hub import DateTime

# 获取当前时间
current_time = DateTime.now()
print(current_time)  # 输出: 2025-12-05T16:11:06+00:00

# 获取特定时区的当前时间
beijing_time = DateTime.now("Asia/Shanghai")
print(beijing_time)  # 输出: 2025-12-06T00:11:06+08:00

# 时区转换
converted_time = DateTime.convert_timezone(
    "07:12",
    "UTC",
    "Asia/Shanghai"
)
print(converted_time)  # 输出: {
#   'source_time': '2025-12-05T07:12:00+00:00',
#   'target_time': '2025-12-05T15:12:00+08:00',
#   'time_difference': '+8.0h',
#   'source_timezone': 'UTC',
#   'target_timezone': 'Asia/Shanghai'
# }
```

## 详细 API

### DateTime 类

`DateTime` 是一个提供日期时间操作和时区转换功能的类。

#### 方法

- `_parse_timezone_offset(timezone_str: str) -> timezone`: 解析时区偏移字符串
- `_get_timezone_obj(tz_str: str)`: 从 IANA 名称或 UTC/GMT 偏移获取时区对象
- `now(timezone_name: Optional[str] = None) -> str`: 获取当前时间，可选择指定时区
- `convert_timezone(time_str: str, from_timezone: str, to_timezone: str, format_str: Optional[str] = None) -> str`: 在时区之间转换时间

## 示例

### 获取当前时间

```python
from toolregistry_hub import DateTime

# 获取 UTC 时间
utc_time = DateTime.now()
print(f"UTC时间: {utc_time}")  # 输出: UTC时间: 2025-12-05T16:11:06+00:00

# 获取北京时间
beijing_time = DateTime.now("Asia/Shanghai")
print(f"北京时间: {beijing_time}")  # 输出: 北京时间: 2025-12-06T00:11:06+08:00

# 获取纽约时间
ny_time = DateTime.now("America/New_York")
print(f"纽约时间: {ny_time}")  # 输出: 纽约时间: 2025-12-05T11:11:06-05:00
```

### 时区转换

```python
from toolregistry_hub import DateTime

# 将 UTC 时间转换为北京时间
beijing_time = DateTime.convert_timezone(
    "07:12",
    "UTC",
    "Asia/Shanghai"
)
print(f"北京时间: {beijing_time}")  # 输出: {
#   'source_time': '2025-12-05T07:12:00+00:00',
#   'target_time': '2025-12-05T15:12:00+08:00',
#   'time_difference': '+8.0h',
#   'source_timezone': 'UTC',
#   'target_timezone': 'Asia/Shanghai'
# }

# 将北京时间转换为纽约时间
ny_time = DateTime.convert_timezone(
    "15:12",
    "Asia/Shanghai",
    "America/New_York"
)
print(f"纽约时间: {ny_time}")  # 输出: {
#   'source_time': '2025-12-06T15:12:00+08:00',
#   'target_time': '2025-12-06T02:12:00-05:00',
#   'time_difference': '-13.0h',
#   'source_timezone': 'Asia/Shanghai',
#   'target_timezone': 'America/New_York'
# }

# 使用自定义格式
formatted_time = DateTime.convert_timezone(
    "15:12",
    "Asia/Shanghai",
    "America/New_York"
)
print(f"格式化的纽约时间: {formatted_time}")  # 输出: {
#   'source_time': '2025-12-06T15:12:00+08:00',
#   'target_time': '2025-12-06T02:12:00-05:00',
#   'time_difference': '-13.0h',
#   'source_timezone': 'Asia/Shanghai',
#   'target_timezone': 'America/New_York'
# }
```

### 支持的时区格式

DateTime 工具支持以下时区格式：

1. IANA 时区名称，例如 "Asia/Shanghai"、"America/New_York"
2. UTC/GMT 偏移量，例如 "UTC+8"、"GMT-5"

```python
from toolregistry_hub import DateTime

# 使用 IANA 时区名称
beijing_time = DateTime.now("Asia/Shanghai")
print(f"北京时间 (IANA): {beijing_time}")  # 输出: 北京时间 (IANA): 2025-12-06T00:11:06+08:00

# 使用 UTC 偏移量
beijing_time_offset = DateTime.now("UTC+8")
print(f"北京时间 (UTC偏移): {beijing_time_offset}")  # 输出: 北京时间 (UTC偏移): 2025-12-06T00:11:06+08:00
```
