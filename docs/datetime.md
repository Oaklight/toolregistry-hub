# 日期时间工具

日期时间工具提供了处理日期、时间和时区转换的功能。

## 类概览

日期时间工具主要包含以下类：

- `DateTime` - 提供日期时间操作和时区转换功能

## 使用方法

### 基本使用

```python
from toolregistry_hub import DateTime

# 获取当前时间
current_time = DateTime.now()
print(current_time)  # 输出: 2025-10-13T07:12:32.841Z

# 获取特定时区的当前时间
beijing_time = DateTime.now("Asia/Shanghai")
print(beijing_time)  # 输出: 2025-10-13T15:12:32.841+08:00

# 时区转换
converted_time = DateTime.convert_timezone(
    "2025-10-13T07:12:32.841Z",
    from_timezone="UTC",
    to_timezone="Asia/Shanghai"
)
print(converted_time)  # 输出: 2025-10-13T15:12:32.841+08:00
```

## 详细 API

### DateTime 类

`DateTime` 是一个提供日期时间操作和时区转换功能的类。

#### 方法

- `_parse_timezone_offset(timezone_str: str) -> timezone`: 解析时区偏移字符串
- `_get_timezone_obj(tz_str: str)`: 从IANA名称或UTC/GMT偏移获取时区对象
- `now(timezone_name: Optional[str] = None) -> str`: 获取当前时间，可选指定时区
- `convert_timezone(time_str: str, from_timezone: str, to_timezone: str, format_str: Optional[str] = None) -> str`: 在时区之间转换时间

## 示例

### 获取当前时间

```python
from toolregistry_hub import DateTime

# 获取UTC当前时间
utc_time = DateTime.now()
print(f"UTC时间: {utc_time}")

# 获取北京时间
beijing_time = DateTime.now("Asia/Shanghai")
print(f"北京时间: {beijing_time}")

# 获取纽约时间
ny_time = DateTime.now("America/New_York")
print(f"纽约时间: {ny_time}")
```

### 时区转换

```python
from toolregistry_hub import DateTime

# 将UTC时间转换为北京时间
beijing_time = DateTime.convert_timezone(
    "2025-10-13T07:12:32.841Z",
    from_timezone="UTC",
    to_timezone="Asia/Shanghai"
)
print(f"北京时间: {beijing_time}")

# 将北京时间转换为纽约时间
ny_time = DateTime.convert_timezone(
    "2025-10-13T15:12:32.841+08:00",
    from_timezone="Asia/Shanghai",
    to_timezone="America/New_York"
)
print(f"纽约时间: {ny_time}")

# 使用自定义格式
formatted_time = DateTime.convert_timezone(
    "2025-10-13T15:12:32.841+08:00",
    from_timezone="Asia/Shanghai",
    to_timezone="America/New_York",
    format_str="%Y-%m-%d %H:%M:%S %Z"
)
print(f"格式化的纽约时间: {formatted_time}")
```

### 支持的时区格式

DateTime工具支持以下时区格式：

1. IANA时区名称，如 "Asia/Shanghai", "America/New_York"
2. UTC/GMT偏移，如 "UTC+8", "GMT-5"

```python
from toolregistry_hub import DateTime

# 使用IANA时区名称
beijing_time = DateTime.now("Asia/Shanghai")
print(f"北京时间 (IANA): {beijing_time}")

# 使用UTC偏移
beijing_time_offset = DateTime.now("UTC+8")
print(f"北京时间 (UTC偏移): {beijing_time_offset}")
```

## 导航

- [返回首页](index.md)
- [查看导航页面](navigation.md)
- [计算器工具](calculator.md)
- [文件操作工具](file_ops.md)
- [文件系统工具](filesystem.md)
- [网络搜索工具](websearch/index.md)
- [单位转换工具](unit_converter.md)
- [其他工具](other_tools.md)