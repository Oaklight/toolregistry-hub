# 计算器工具

计算器工具提供了各种数学计算功能，从基本的算术运算到更复杂的数学函数。

## 类概览

计算器工具主要包含以下类：

- `BaseCalculator` - 提供核心数学操作的基类
- `Calculator` - 提供数学计算功能的主类，包括表达式求值

## 使用方法

### 基本使用

```python
from toolregistry_hub import Calculator

# 计算表达式
result = Calculator.evaluate("2 + 3 * 4")
print(result)  # 输出: 14

# 获取帮助信息
help_info = Calculator.help("sqrt")
print(help_info)

# 列出所有可用函数
functions = Calculator.list_allowed_fns(with_help=True)
print(functions)
```

### 支持的操作

计算器支持以下操作：

#### 基本算术

- 加法 (`add`, `+`)
- 减法 (`subtract`, `-`)
- 乘法 (`multiply`, `*`)
- 除法 (`divide`, `/`)
- 整除 (`floor_divide`, `//`)
- 取模 (`mod`, `%`)
- 绝对值 (`abs`)
- 幂运算 (`pow`, `**`)

#### 高级数学函数

- 平方根 (`sqrt`)
- 对数 (`log`, `ln`)
- 指数 (`exp`)
- 三角函数 (未实现)

#### 统计函数

- 最小值 (`min`)
- 最大值 (`max`)
- 求和 (`sum`)
- 平均值 (`average`)
- 中位数 (`median`)
- 众数 (`mode`)
- 标准差 (`standard_deviation`)

#### 其他函数

- 阶乘 (`factorial`)
- 最大公约数 (`gcd`)
- 最小公倍数 (`lcm`)
- 距离计算 (`dist`)
- 简单利息计算 (`simple_interest`)
- 复利计算 (`compound_interest`)

## 详细 API

### BaseCalculator 类

`BaseCalculator` 是一个提供核心数学操作的基类。

#### 方法

- `add(a: float, b: float) -> float`: 返回两个数的和
- `subtract(a: float, b: float) -> float`: 返回两个数的差
- `multiply(a: float, b: float) -> float`: 返回两个数的积
- `divide(a: float, b: float) -> float`: 返回两个数的商
- `floor_divide(a: float, b: float) -> float`: 返回两个数的整除结果
- `mod(a: float, b: float) -> float`: 返回两个数的模
- `abs(x: float) -> float`: 返回一个数的绝对值
- `pow(base: float, exponent: float) -> float`: 返回 base 的 exponent 次幂
- `sqrt(x: float) -> float`: 返回一个数的平方根
- `log(x: float, base: float = 10) -> float`: 返回以 base 为底 x 的对数
- `ln(x: float) -> float`: 返回 x 的自然对数
- `exp(x: float) -> float`: 返回 e 的 x 次幂
- `min(numbers: List[float]) -> float`: 返回一组数中的最小值
- `max(numbers: List[float]) -> float`: 返回一组数中的最大值
- `sum(numbers: List[float]) -> float`: 返回一组数的和
- `average(numbers: List[float]) -> float`: 返回一组数的平均值
- `median(numbers: List[float]) -> float`: 返回一组数的中位数
- `mode(numbers: List[float]) -> List[float]`: 返回一组数的众数
- `standard_deviation(numbers: List[float]) -> float`: 返回一组数的标准差
- `factorial(n: int) -> int`: 返回 n 的阶乘
- `gcd(a: int, b: int) -> int`: 返回两个数的最大公约数
- `lcm(a: int, b: int) -> int`: 返回两个数的最小公倍数
- `dist(p1: List[float], p2: List[float], p: int = 2) -> float`: 计算两点之间的距离
- `simple_interest(principal: float, rate: float, time: float) -> float`: 计算简单利息
- `compound_interest(principal: float, rate: float, time: float, n: int = 1) -> float`: 计算复利

### Calculator 类

`Calculator` 是提供数学计算功能的主类，包括表达式求值。

#### 方法

- `list_allowed_fns(with_help: bool = False) -> str`: 列出所有允许的函数
- `help(fn_name: str) -> str`: 获取特定函数的帮助信息
- `evaluate(expression: str) -> Union[float, int, bool]`: 计算数学表达式的值

## 示例

### 计算表达式

```python
from toolregistry_hub import Calculator

# 基本算术
result = Calculator.evaluate("2 + 3 * 4")
print(result)  # 输出: 14

# 使用函数
result = Calculator.evaluate("sqrt(16) + pow(2, 3)")
print(result)  # 输出: 12.0

# 混合使用函数和运算符
result = Calculator.evaluate("sqrt(16) + 2 ** 3")
print(result)  # 输出: 12.0
```

### 获取帮助信息

```python
from toolregistry_hub import Calculator

# 获取特定函数的帮助信息
help_info = Calculator.help("sqrt")
print(help_info)

# 列出所有可用函数
functions = Calculator.list_allowed_fns(with_help=True)
print(functions)
```

## 导航

- [返回首页](index.md)
- [查看导航页面](navigation.md)
- [日期时间工具](datetime.md)
- [文件操作工具](file_ops.md)
- [文件系统工具](filesystem.md)
- [网络搜索工具](websearch/index.md)
- [单位转换工具](unit_converter.md)
- [其他工具](other_tools.md)