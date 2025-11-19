# 单位转换工具

单位转换工具提供了各种单位之间的转换功能，包括长度、质量、温度、时间等。

## 类概览

单位转换工具主要包含以下类：

- `UnitConverter` - 提供各种单位转换功能的类

## 使用方法

### 基本使用

```python
from toolregistry_hub import UnitConverter

# 长度转换
meters = UnitConverter.feet_to_meters(10)
print(f"10英尺 = {meters}米")

# 温度转换
celsius = UnitConverter.fahrenheit_to_celsius(98.6)
print(f"98.6华氏度 = {celsius}摄氏度")

# 质量转换
kilograms = UnitConverter.pounds_to_kilograms(150)
print(f"150磅 = {kilograms}千克")
```

## 详细 API

### UnitConverter 类

`UnitConverter` 是一个提供各种单位转换功能的类。

#### 长度转换方法

- `meters_to_feet(meters: float) -> float`: 将米转换为英尺
- `feet_to_meters(feet: float) -> float`: 将英尺转换为米
- `kilometers_to_miles(kilometers: float) -> float`: 将千米转换为英里
- `miles_to_kilometers(miles: float) -> float`: 将英里转换为千米
- `inches_to_centimeters(inches: float) -> float`: 将英寸转换为厘米
- `centimeters_to_inches(centimeters: float) -> float`: 将厘米转换为英寸
- `meters_to_yards(meters: float) -> float`: 将米转换为码
- `yards_to_meters(yards: float) -> float`: 将码转换为米

#### 质量转换方法

- `kilograms_to_pounds(kilograms: float) -> float`: 将千克转换为磅
- `pounds_to_kilograms(pounds: float) -> float`: 将磅转换为千克
- `grams_to_ounces(grams: float) -> float`: 将克转换为盎司
- `ounces_to_grams(ounces: float) -> float`: 将盎司转换为克
- `kilograms_to_stones(kilograms: float) -> float`: 将千克转换为英石
- `stones_to_kilograms(stones: float) -> float`: 将英石转换为千克

#### 温度转换方法

- `celsius_to_fahrenheit(celsius: float) -> float`: 将摄氏度转换为华氏度
- `fahrenheit_to_celsius(fahrenheit: float) -> float`: 将华氏度转换为摄氏度
- `celsius_to_kelvin(celsius: float) -> float`: 将摄氏度转换为开尔文
- `kelvin_to_celsius(kelvin: float) -> float`: 将开尔文转换为摄氏度
- `fahrenheit_to_kelvin(fahrenheit: float) -> float`: 将华氏度转换为开尔文
- `kelvin_to_fahrenheit(kelvin: float) -> float`: 将开尔文转换为华氏度

#### 体积转换方法

- `liters_to_gallons(liters: float) -> float`: 将升转换为加仑
- `gallons_to_liters(gallons: float) -> float`: 将加仑转换为升
- `cubic_meters_to_cubic_feet(cubic_meters: float) -> float`: 将立方米转换为立方英尺
- `cubic_feet_to_cubic_meters(cubic_feet: float) -> float`: 将立方英尺转换为立方米
- `milliliters_to_fluid_ounces(milliliters: float) -> float`: 将毫升转换为液量盎司
- `fluid_ounces_to_milliliters(fluid_ounces: float) -> float`: 将液量盎司转换为毫升

#### 面积转换方法

- `square_meters_to_square_feet(square_meters: float) -> float`: 将平方米转换为平方英尺
- `square_feet_to_square_meters(square_feet: float) -> float`: 将平方英尺转换为平方米
- `hectares_to_acres(hectares: float) -> float`: 将公顷转换为英亩
- `acres_to_hectares(acres: float) -> float`: 将英亩转换为公顷

#### 速度转换方法

- `kilometers_per_hour_to_miles_per_hour(kph: float) -> float`: 将千米/小时转换为英里/小时
- `miles_per_hour_to_kilometers_per_hour(mph: float) -> float`: 将英里/小时转换为千米/小时
- `meters_per_second_to_feet_per_second(mps: float) -> float`: 将米/秒转换为英尺/秒
- `feet_per_second_to_meters_per_second(fps: float) -> float`: 将英尺/秒转换为米/秒

#### 能量转换方法

- `joules_to_calories(joules: float) -> float`: 将焦耳转换为卡路里
- `calories_to_joules(calories: float) -> float`: 将卡路里转换为焦耳
- `kilowatt_hours_to_megajoules(kwh: float) -> float`: 将千瓦时转换为兆焦
- `megajoules_to_kilowatt_hours(mj: float) -> float`: 将兆焦转换为千瓦时

#### 压力转换方法

- `pascals_to_psi(pascals: float) -> float`: 将帕斯卡转换为磅/平方英寸
- `psi_to_pascals(psi: float) -> float`: 将磅/平方英寸转换为帕斯卡
- `bars_to_atmospheres(bars: float) -> float`: 将巴转换为标准大气压
- `atmospheres_to_bars(atmospheres: float) -> float`: 将标准大气压转换为巴

#### 电磁单位转换方法

- `weber_to_tesla(weber: float, area: float = 1.0) -> float`: 将韦伯转换为特斯拉
- `tesla_to_weber(tesla: float, area: float = 1.0) -> float`: 将特斯拉转换为韦伯

## 示例

### 长度转换

```python
from toolregistry_hub import UnitConverter

# 英尺到米
meters = UnitConverter.feet_to_meters(10)
print(f"10英尺 = {meters}米")

# 英里到千米
kilometers = UnitConverter.miles_to_kilometers(5)
print(f"5英里 = {kilometers}千米")

# 厘米到英寸
inches = UnitConverter.centimeters_to_inches(30)
print(f"30厘米 = {inches}英寸")
```

### 质量转换

```python
from toolregistry_hub import UnitConverter

# 千克到磅
pounds = UnitConverter.kilograms_to_pounds(70)
print(f"70千克 = {pounds}磅")

# 盎司到克
grams = UnitConverter.ounces_to_grams(16)
print(f"16盎司 = {grams}克")

# 英石到千克
kilograms = UnitConverter.stones_to_kilograms(10)
print(f"10英石 = {kilograms}千克")
```

### 温度转换

```python
from toolregistry_hub import UnitConverter

# 摄氏度到华氏度
fahrenheit = UnitConverter.celsius_to_fahrenheit(25)
print(f"25摄氏度 = {fahrenheit}华氏度")

# 华氏度到摄氏度
celsius = UnitConverter.fahrenheit_to_celsius(98.6)
print(f"98.6华氏度 = {celsius}摄氏度")

# 摄氏度到开尔文
kelvin = UnitConverter.celsius_to_kelvin(0)
print(f"0摄氏度 = {kelvin}开尔文")
```

### 体积转换

```python
from toolregistry_hub import UnitConverter

# 升到加仑
gallons = UnitConverter.liters_to_gallons(10)
print(f"10升 = {gallons}加仑")

# 立方米到立方英尺
cubic_feet = UnitConverter.cubic_meters_to_cubic_feet(2)
print(f"2立方米 = {cubic_feet}立方英尺")

# 液量盎司到毫升
milliliters = UnitConverter.fluid_ounces_to_milliliters(8)
print(f"8液量盎司 = {milliliters}毫升")
```

## 导航

- [返回首页](index.md)
- [查看导航页面](navigation.md)
- [计算器工具](calculator.md)
- [日期时间工具](datetime.md)
- [文件操作工具](file_ops.md)
- [文件系统工具](filesystem.md)
- [网络搜索工具](websearch/index.md)
- [其他工具](other_tools.md)
