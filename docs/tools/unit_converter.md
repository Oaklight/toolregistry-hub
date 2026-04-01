---
title: 单位转换工具
summary: 支持各种测量系统的综合单位转换功能
description: 完整的单位转换工具，支持温度、长度、重量、时间、容量、面积、速度、数据存储、压力、功率、能量等多种测量类型。
keywords: 单位转换器, 测量转换, 温度, 长度, 重量, 时间, 数据转换
author: Oaklight
---

# 单位转换工具

单位转换工具提供各种测量系统的综合单位转换功能。这些工具支持多个类别之间的转换，包括温度、长度、重量、时间、容量、面积、速度、数据存储、压力、功率、能量等。

!!! note "API 变化提示 (v0.5.2+)"
    从 v0.5.2 版本开始，UnitConverter 的 API 发生了重大变化。不再直接暴露所有转换方法（如 `celsius_to_fahrenheit()`），而是通过统一的 `convert()` 方法进行调用。这样做是为了减少 LLM 工具字段的长度，提高性能。
    
    **旧版本用法** (v0.5.1 及更早):
    ```python
    result = UnitConverter.celsius_to_fahrenheit(25)
    ```
    
    **新版本用法** (v0.5.2+):
    ```python
    result = UnitConverter.convert(25, "celsius_to_fahrenheit")
    ```
    
    所有转换功能保持不变，只是调用方式有所改变。

## 概述

UnitConverter 类提供不同测量单位之间的精确转换：

- **温度**：摄氏度、华氏度、开尔文
- **长度**：米、英尺、英寸、厘米
- **重量**：千克、磅
- **时间**：秒、分钟、小时
- **容量**：升、加仑
- **面积**：平方米、平方英尺
- **速度**：km/h、mph
- **数据存储**：比特、字节、千字节、兆字节
- **压力**：帕斯卡、巴、大气压
- **功率**：瓦特、千瓦、马力
- **能量**：焦耳、卡路里、千瓦时
- **频率**：赫兹、千赫兹、兆赫兹
- **燃油经济性**：km/L、mpg
- **电学**：安培、伏特、欧姆
- **磁学**：韦伯、特斯拉、高斯
- **辐射**：戈瑞、希沃特
- **光强度**：勒克斯、流明

## 快速开始

```python
from toolregistry_hub import UnitConverter

# 温度转换
celsius = UnitConverter.convert(98.6, "fahrenheit_to_celsius")
print(f"98.6°F = {celsius:.1f}°C")

# 长度转换
feet = UnitConverter.convert(2.5, "meters_to_feet")
print(f"2.5米 = {feet:.2f}英尺")

# 重量转换
pounds = UnitConverter.convert(70, "kilograms_to_pounds")
print(f"70千克 = {pounds:.1f}磅")

# 查看所有可用的转换函数
import json
conversions = json.loads(UnitConverter.list_conversions("all"))
print(f"可用转换: {len(conversions)}个")

# 按类别查看转换函数
temp_conversions = json.loads(UnitConverter.list_conversions("temperature"))
print(f"温度转换: {temp_conversions}")

# 获取特定转换函数的帮助
help_text = UnitConverter.help("celsius_to_fahrenheit")
print(help_text)
```

## 转换类别

### 温度转换

| 从 → 到         | 转换函数名                | 公式/转换因子        | 示例                                                      |
| --------------- | ------------------------- | -------------------- | --------------------------------------------------------- |
| 摄氏度 → 华氏度 | `celsius_to_fahrenheit`   | °F = (°C × 9/5) + 32 | `UnitConverter.convert(25, "celsius_to_fahrenheit") = 77.0` |
| 华氏度 → 摄氏度 | `fahrenheit_to_celsius`   | °C = (°F - 32) × 5/9 | `UnitConverter.convert(77, "fahrenheit_to_celsius") = 25.0` |
| 开尔文 → 摄氏度 | `kelvin_to_celsius`       | °C = K - 273.15      | `UnitConverter.convert(298.15, "kelvin_to_celsius") = 25.0` |
| 摄氏度 → 开尔文 | `celsius_to_kelvin`       | K = °C + 273.15      | `UnitConverter.convert(25, "celsius_to_kelvin") = 298.15`   |

### 长度转换

| 从 → 到     | 方法                      | 转换因子               | 示例                                               |
| ----------- | ------------------------- | ---------------------- | -------------------------------------------------- |
| 米 → 英尺   | `meters_to_feet()`        | 1 米 = 3.28084 英尺    | `UnitConverter.meters_to_feet(1) = 3.28084`        |
| 英尺 → 米   | `feet_to_meters()`        | 1 英尺 = 0.3048 米     | `UnitConverter.feet_to_meters(10) = 3.048`         |
| 厘米 → 英寸 | `centimeters_to_inches()` | 1 厘米 = 0.393701 英寸 | `UnitConverter.centimeters_to_inches(25.4) = 10.0` |
| 英寸 → 厘米 | `inches_to_centimeters()` | 1 英寸 = 2.54 厘米     | `UnitConverter.inches_to_centimeters(12) = 30.48`  |

### 重量转换

| 从 → 到   | 方法                    | 转换因子             | 示例                                              |
| --------- | ----------------------- | -------------------- | ------------------------------------------------- |
| 千克 → 磅 | `kilograms_to_pounds()` | 1 千克 = 2.20462 磅  | `UnitConverter.kilograms_to_pounds(1) = 2.20462`  |
| 磅 → 千克 | `pounds_to_kilograms()` | 1 磅 = 0.453592 千克 | `UnitConverter.pounds_to_kilograms(10) = 4.53592` |

### 时间转换

| 从 → 到   | 方法                   | 转换因子       | 示例                                            |
| --------- | ---------------------- | -------------- | ----------------------------------------------- |
| 秒 → 分钟 | `seconds_to_minutes()` | 1 分钟 = 60 秒 | `UnitConverter.seconds_to_minutes(180) = 3.0`   |
| 分钟 → 秒 | `minutes_to_seconds()` | 1 分钟 = 60 秒 | `UnitConverter.minutes_to_seconds(2.5) = 150.0` |

### 容量转换

| 从 → 到   | 方法                  | 转换因子            | 示例                                            |
| --------- | --------------------- | ------------------- | ----------------------------------------------- |
| 升 → 加仑 | `liters_to_gallons()` | 1 加仑 = 3.78541 升 | `UnitConverter.liters_to_gallons(10) = 2.64172` |
| 加仑 → 升 | `gallons_to_liters()` | 1 加仑 = 3.78541 升 | `UnitConverter.gallons_to_liters(1) = 3.78541`  |

### 面积转换

| 从 → 到           | 方法                             | 转换因子                     | 示例                                                       |
| ----------------- | -------------------------------- | ---------------------------- | ---------------------------------------------------------- |
| 平方米 → 平方英尺 | `square_meters_to_square_feet()` | 1 平方米 = 10.7639 平方英尺  | `UnitConverter.square_meters_to_square_feet(1) = 10.7639`  |
| 平方英尺 → 平方米 | `square_feet_to_square_meters()` | 1 平方英尺 = 0.092903 平方米 | `UnitConverter.square_feet_to_square_meters(10) = 0.92903` |

### 速度转换

| 从 → 到    | 方法           | 转换因子                        | 示例                                      |
| ---------- | -------------- | ------------------------------- | ----------------------------------------- |
| km/h → mph | `kmh_to_mph()` | 1 英里/小时 = 1.60934 千米/小时 | `UnitConverter.kmh_to_mph(100) = 62.1371` |
| mph → km/h | `mph_to_kmh()` | 1 英里/小时 = 1.60934 千米/小时 | `UnitConverter.mph_to_kmh(60) = 96.5606`  |

### 数据存储转换

| 从 → 到         | 方法                       | 转换因子               | 示例                                               |
| --------------- | -------------------------- | ---------------------- | -------------------------------------------------- |
| 比特 → 字节     | `bits_to_bytes()`          | 1 字节 = 8 比特        | `UnitConverter.bits_to_bytes(8) = 1.0`             |
| 字节 → 千字节   | `bytes_to_kilobytes()`     | 1 千字节 = 1024 字节   | `UnitConverter.bytes_to_kilobytes(1024) = 1.0`     |
| 千字节 → 兆字节 | `kilobytes_to_megabytes()` | 1 兆字节 = 1024 千字节 | `UnitConverter.kilobytes_to_megabytes(1024) = 1.0` |

### 压力转换

| 从 → 到     | 方法              | 转换因子              | 示例                                        |
| ----------- | ----------------- | --------------------- | ------------------------------------------- |
| 帕斯卡 → 巴 | `pascal_to_bar()` | 1 巴 = 100,000 帕斯卡 | `UnitConverter.pascal_to_bar(100000) = 1.0` |
| 巴 → 大气压 | `bar_to_atm()`    | 1 大气压 = 1.01325 巴 | `UnitConverter.bar_to_atm(1.01325) = 1.0`   |

### 功率转换

| 从 → 到     | 方法                        | 转换因子             | 示例                                                 |
| ----------- | --------------------------- | -------------------- | ---------------------------------------------------- |
| 瓦特 → 千瓦 | `watts_to_kilowatts()`      | 1 千瓦 = 1000 瓦特   | `UnitConverter.watts_to_kilowatts(1500) = 1.5`       |
| 千瓦 → 马力 | `kilowatts_to_horsepower()` | 1 马力 = 0.7457 千瓦 | `UnitConverter.kilowatts_to_horsepower(1) = 1.34102` |

### 能量转换

| 从 → 到         | 方法                           | 转换因子                  | 示例                                                     |
| --------------- | ------------------------------ | ------------------------- | -------------------------------------------------------- |
| 焦耳 → 卡路里   | `joules_to_calories()`         | 1 卡路里 = 4.184 焦耳     | `UnitConverter.joules_to_calories(4184) = 1000.0`        |
| 卡路里 → 千瓦时 | `calories_to_kilowatt_hours()` | 1 千瓦时 = 860,421 卡路里 | `UnitConverter.calories_to_kilowatt_hours(860421) = 1.0` |

### 频率转换

| 从 → 到         | 方法                       | 转换因子               | 示例                                               |
| --------------- | -------------------------- | ---------------------- | -------------------------------------------------- |
| 赫兹 → 千赫兹   | `hertz_to_kilohertz()`     | 1 千赫兹 = 1000 赫兹   | `UnitConverter.hertz_to_kilohertz(1000) = 1.0`     |
| 千赫兹 → 兆赫兹 | `kilohertz_to_megahertz()` | 1 兆赫兹 = 1000 千赫兹 | `UnitConverter.kilohertz_to_megahertz(1000) = 1.0` |

### 燃油经济性转换

| 从 → 到    | 方法                    | 转换因子                       | 示例                                            |
| ---------- | ----------------------- | ------------------------------ | ----------------------------------------------- |
| km/L → mpg | `km_per_liter_to_mpg()` | 1 英里/加仑 = 0.425144 千米/升 | `UnitConverter.km_per_liter_to_mpg(12) = 28.24` |
| mpg → km/L | `mpg_to_km_per_liter()` | 1 英里/加仑 = 0.425144 千米/升 | `UnitConverter.mpg_to_km_per_liter(30) = 12.75` |

### 电学转换

| 从 → 到     | 方法                      | 转换因子           | 示例                                              |
| ----------- | ------------------------- | ------------------ | ------------------------------------------------- |
| 安培 → 毫安 | `ampere_to_milliampere()` | 1 安培 = 1000 毫安 | `UnitConverter.ampere_to_milliampere(1) = 1000.0` |
| 伏特 → 千伏 | `volt_to_kilovolt()`      | 1 千伏 = 1000 伏特 | `UnitConverter.volt_to_kilovolt(1000) = 1.0`      |
| 欧姆 → 千欧 | `ohm_to_kiloohm()`        | 1 千欧 = 1000 欧姆 | `UnitConverter.ohm_to_kiloohm(1000) = 1.0`        |

### 磁学转换

| 从 → 到       | 方法               | 公式/转换因子              | 示例                                        |
| ------------- | ------------------ | -------------------------- | ------------------------------------------- |
| 韦伯 → 特斯拉 | `weber_to_tesla()` | B = Φ/A (A 为平方米面积)   | `UnitConverter.weber_to_tesla(1, 1) = 1.0`  |
| 高斯 → 特斯拉 | `gauss_to_tesla()` | 1 特斯拉 = 10,000 高斯     | `UnitConverter.gauss_to_tesla(10000) = 1.0` |
| 特斯拉 → 韦伯 | `tesla_to_weber()` | Φ = B × A (A 为平方米面积) | `UnitConverter.tesla_to_weber(1, 1) = 1.0`  |
| 特斯拉 → 高斯 | `tesla_to_gauss()` | 1 特斯拉 = 10,000 高斯     | `UnitConverter.tesla_to_gauss(1) = 10000.0` |

### 辐射转换

| 从 → 到       | 方法                | 说明                                    | 示例                                     |
| ------------- | ------------------- | --------------------------------------- | ---------------------------------------- |
| 戈瑞 → 希沃特 | `gray_to_sievert()` | 对于大多数类型的辐射，1 戈瑞 = 1 希沃特 | `UnitConverter.gray_to_sievert(1) = 1.0` |

### 光强度转换

| 从 → 到       | 方法             | 公式                         | 示例                                         |
| ------------- | ---------------- | ---------------------------- | -------------------------------------------- |
| 勒克斯 → 流明 | `lux_to_lumen()` | 流明 = 勒克斯 × 面积(平方米) | `UnitConverter.lux_to_lumen(100, 2) = 200.0` |
| 流明 → 勒克斯 | `lumen_to_lux()` | 勒克斯 = 流明 / 面积(平方米) | `UnitConverter.lumen_to_lux(200, 2) = 100.0` |

## 实际示例

### 烹饪转换

```python
from toolregistry_hub import UnitConverter

# 食谱转换
oven_temp_f = 350  # 350°F用于烘焙
oven_temp_c = UnitConverter.convert(oven_temp_f, "fahrenheit_to_celsius")
print(f"预热烤箱至 {oven_temp_c:.0f}°C")
# 输出: 预热烤箱至 177°C

# 液体测量
ml_in_cup = 240
cups = 2.5
ml = cups * ml_in_cup
print(f"{cups}杯 = {ml}毫升")
# 输出: 2.5杯 = 600.0毫升

# 重量转换
pounds = 1.5  # 1.5磅肉
kg = UnitConverter.convert(pounds, "pounds_to_kilograms")
print(f"{pounds}磅 = {kg:.3f}千克")
# 输出: 1.5磅 = 0.680千克
```

### 旅行转换

```python
from toolregistry_hub import UnitConverter

# 距离转换
kmh = 100  # 限速为km/h
mph = UnitConverter.convert(kmh, "kmh_to_mph")
print(f"限速：{kmh} km/h = {mph:.1f} mph")
# 输出: 限速：100 km/h = 62.1 mph

# 燃油效率
km_per_l = 12  # 12 km/L燃油效率
mpg = UnitConverter.convert(km_per_l, "km_per_liter_to_mpg")
print(f"燃油效率：{km_per_l} km/L = {mpg:.1f} mpg")
# 输出: 燃油效率：12 km/L = 28.2 mpg

# 温度转换
weather_c = 22  # 摄氏度天气
weather_f = UnitConverter.convert(weather_c, "celsius_to_fahrenheit")
print(f"天气：{weather_c}°C = {weather_f}°F")
# 输出: 天气：22°C = 71.6°F
```

### 科学计算

```python
from toolregistry_hub import UnitConverter

# 电气计算
voltage_v = 132000  # 高压线路（伏特）
voltage_kv = UnitConverter.convert(voltage_v, "volt_to_kilovolt")
print(f"电压：{voltage_v} V = {voltage_kv} kV")
# 输出: 电压：132000 V = 132.0 kV

# 数据存储
bytes_data = 1024 * 1024 * 500  # 500 MB的字节数
kb_data = UnitConverter.convert(bytes_data, "bytes_to_kilobytes")
mb_data = UnitConverter.convert(kb_data, "kilobytes_to_megabytes")
print(f"数据大小：{bytes_data}字节 = {mb_data} MB")
# 输出: 数据大小：524288000字节 = 500.0 MB

# 压力转换
pressure_bar = 2.5  # 巴压力
pressure_atm = UnitConverter.convert(pressure_bar, "bar_to_atm")
print(f"压力：{pressure_bar} bar = {pressure_atm:.2f} atm")
# 输出: 压力：2.5 bar = 2.47 atm
```

### 工程转换

```python
from toolregistry_hub import UnitConverter

# 材料尺寸
length_ft = 10.5  # 英尺长度
length_m = UnitConverter.convert(length_ft, "feet_to_meters")
print(f"长度：{length_ft}英尺 = {length_m:.3f}米")
# 输出: 长度：10.5英尺 = 3.200米

# 面积计算
area_sqm = 150  # 平方米面积
area_sqft = UnitConverter.convert(area_sqm, "square_meters_to_square_feet")
print(f"面积：{area_sqm}平方米 = {area_sqft:.1f}平方英尺")
# 输出: 面积：150平方米 = 1614.6平方英尺

# 功率计算
kilowatts = 186  # 发动机功率，单位为千瓦
horsepower = UnitConverter.convert(kilowatts, "kilowatts_to_horsepower")
print(f"功率：{kilowatts}千瓦 = {horsepower:.1f}马力")
# 输出: 功率：186千瓦 = 249.4马力

# 带额外参数的转换（如光强度转换）
lux_value = 100
area = 2  # 平方米
lumens = UnitConverter.convert(lux_value, "lux_to_lumen", area=area)
print(f"光通量：{lux_value} lux × {area} m² = {lumens} lumens")
# 输出: 光通量：100 lux × 2 m² = 200.0 lumens
```

## 重要说明

### 精度和准确性

- **四舍五入**：由于浮点运算，结果可能存在微小的舍入误差
- **转换因子**：基于国际标准
- **温度**：开尔文使用 273.15 作为与摄氏度的偏移量

### 面积和体积

- **面积转换**：假设为平方单位（m² 到 ft²）
- **体积转换**：使用升和加仑进行液体测量

### 磁学转换

- **面积参数**：韦伯 ↔ 特斯拉转换需要面积参数
- **默认面积**：未指定时为 1.0 平方米

### 数据存储

- **二进制系统**：使用 1024 为基础的转换（KiB、MiB、GiB）
- **非十进制**：与 SI 前缀不同（KB、MB、GB）

## 转换表

### 快速参考

| 类别     | 常见转换                                  |
| -------- | ----------------------------------------- |
| **温度** | 0°C = 32°F = 273.15K                      |
| **长度** | 1 英寸 = 2.54 厘米，1 英里 = 1.609 千米   |
| **重量** | 1 千克 = 2.205 磅，1 盎司 = 28.35 克      |
| **体积** | 1 加仑 = 3.785 升，1 夸脱 = 0.946 升      |
| **速度** | 100 km/h = 62.1 mph                       |
| **面积** | 1 英亩 = 4047 平方米，1 公顷 = 2.471 英亩 |
