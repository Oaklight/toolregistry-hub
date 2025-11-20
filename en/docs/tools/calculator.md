# Calculator Tools

The calculator tools provide various mathematical calculation functions, from basic arithmetic operations to more complex mathematical functions.

## Class Overview

The calculator tools mainly include the following classes:

- `BaseCalculator` - Base class providing core mathematical operations
- `Calculator` - Main class providing mathematical calculation functions, including expression evaluation

## Usage

### Basic Usage

```python
from toolregistry_hub import Calculator

# Calculate expressions
result = Calculator.evaluate("2 + 3 * 4")
print(result)  # Output: 14

# Get help information
help_info = Calculator.help("sqrt")
print(help_info)

# List all available functions
functions = Calculator.list_allowed_fns(with_help=True)
print(functions)
```

### Supported Operations

The calculator supports the following operations:

#### Basic Arithmetic

- Addition (`add`, `+`)
- Subtraction (`subtract`, `-`)
- Multiplication (`multiply`, `*`)
- Division (`divide`, `/`)
- Floor division (`floor_divide`, `//`)
- Modulo (`mod`, `%`)
- Absolute value (`abs`)
- Power operation (`pow`, `**`)

#### Advanced Mathematical Functions

- Square root (`sqrt`)
- Logarithm (`log`, `ln`)
- Exponential (`exp`)
- Trigonometric functions (not implemented)

#### Statistical Functions

- Minimum (`min`)
- Maximum (`max`)
- Sum (`sum`)
- Average (`average`)
- Median (`median`)
- Mode (`mode`)
- Standard deviation (`standard_deviation`)

#### Other Functions

- Factorial (`factorial`)
- Greatest common divisor (`gcd`)
- Least common multiple (`lcm`)
- Distance calculation (`dist`)
- Simple interest calculation (`simple_interest`)
- Compound interest calculation (`compound_interest`)

## Detailed API

### BaseCalculator Class

`BaseCalculator` is a base class that provides core mathematical operations.

#### Methods

- `add(a: float, b: float) -> float`: Returns the sum of two numbers
- `subtract(a: float, b: float) -> float`: Returns the difference of two numbers
- `multiply(a: float, b: float) -> float`: Returns the product of two numbers
- `divide(a: float, b: float) -> float`: Returns the quotient of two numbers
- `floor_divide(a: float, b: float) -> float`: Returns the floor division result of two numbers
- `mod(a: float, b: float) -> float`: Returns the modulo of two numbers
- `abs(x: float) -> float`: Returns the absolute value of a number
- `pow(base: float, exponent: float) -> float`: Returns base raised to the power of exponent
- `sqrt(x: float) -> float`: Returns the square root of a number
- `log(x: float, base: float = 10) -> float`: Returns the logarithm of x with base
- `ln(x: float) -> float`: Returns the natural logarithm of x
- `exp(x: float) -> float`: Returns e raised to the power of x
- `min(numbers: List[float]) -> float`: Returns the minimum value from a list of numbers
- `max(numbers: List[float]) -> float`: Returns the maximum value from a list of numbers
- `sum(numbers: List[float]) -> float`: Returns the sum of a list of numbers
- `average(numbers: List[float]) -> float`: Returns the average of a list of numbers
- `median(numbers: List[float]) -> float`: Returns the median of a list of numbers
- `mode(numbers: List[float]) -> List[float]`: Returns the mode of a list of numbers
- `standard_deviation(numbers: List[float]) -> float`: Returns the standard deviation of a list of numbers
- `factorial(n: int) -> int`: Returns the factorial of n
- `gcd(a: int, b: int) -> int`: Returns the greatest common divisor of two numbers
- `lcm(a: int, b: int) -> int`: Returns the least common multiple of two numbers
- `dist(p1: List[float], p2: List[float], p: int = 2) -> float`: Calculates the distance between two points
- `simple_interest(principal: float, rate: float, time: float) -> float`: Calculates simple interest
- `compound_interest(principal: float, rate: float, time: float, n: int = 1) -> float`: Calculates compound interest

### Calculator Class

`Calculator` is the main class that provides mathematical calculation functions, including expression evaluation.

#### Methods

- `list_allowed_fns(with_help: bool = False) -> str`: Lists all allowed functions
- `help(fn_name: str) -> str`: Gets help information for a specific function
- `evaluate(expression: str) -> Union[float, int, bool]`: Evaluates the value of a mathematical expression

## Examples

### Calculating Expressions

```python
from toolregistry_hub import Calculator

# Basic arithmetic
result = Calculator.evaluate("2 + 3 * 4")
print(result)  # Output: 14

# Using functions
result = Calculator.evaluate("sqrt(16) + pow(2, 3)")
print(result)  # Output: 12.0

# Mixed use of functions and operators
result = Calculator.evaluate("sqrt(16) + 2 ** 3")
print(result)  # Output: 12.0
```

### Getting Help Information

```python
from toolregistry_hub import Calculator

# Get help information for a specific function
help_info = Calculator.help("sqrt")
print(help_info)

# List all available functions
functions = Calculator.list_allowed_fns(with_help=True)
print(functions)
```
