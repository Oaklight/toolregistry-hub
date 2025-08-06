"""Unit tests for Calculator module."""

import math

import pytest

from toolregistry_hub.calculator import BaseCalculator, Calculator


class TestBaseCalculator:
    """Test cases for BaseCalculator class."""

    def test_add(self):
        """Test addition operation."""
        assert BaseCalculator.add(2, 3) == 5
        assert BaseCalculator.add(-1, 1) == 0
        assert BaseCalculator.add(0.1, 0.2) == pytest.approx(0.3)

    def test_subtract(self):
        """Test subtraction operation."""
        assert BaseCalculator.subtract(5, 3) == 2
        assert BaseCalculator.subtract(1, 1) == 0
        assert BaseCalculator.subtract(-1, -1) == 0

    def test_multiply(self):
        """Test multiplication operation."""
        assert BaseCalculator.multiply(3, 4) == 12
        assert BaseCalculator.multiply(-2, 3) == -6
        assert BaseCalculator.multiply(0, 5) == 0

    def test_divide(self):
        """Test division operation."""
        assert BaseCalculator.divide(10, 2) == 5
        assert BaseCalculator.divide(7, 2) == 3.5

        with pytest.raises(ValueError, match="Cannot divide by zero"):
            BaseCalculator.divide(5, 0)

    def test_floor_divide(self):
        """Test floor division operation."""
        assert BaseCalculator.floor_divide(10, 3) == 3
        assert BaseCalculator.floor_divide(7, 2) == 3

        with pytest.raises(ValueError, match="Cannot divide by zero"):
            BaseCalculator.floor_divide(5, 0)

    def test_mod(self):
        """Test modulo operation."""
        assert BaseCalculator.mod(10, 3) == 1
        assert BaseCalculator.mod(8, 4) == 0

        with pytest.raises(ValueError, match="Cannot divide by zero"):
            BaseCalculator.mod(5, 0)

    def test_abs(self):
        """Test absolute value operation."""
        assert BaseCalculator.abs(-5) == 5
        assert BaseCalculator.abs(5) == 5
        assert BaseCalculator.abs(0) == 0

    def test_round(self):
        """Test rounding operation."""
        assert BaseCalculator.round(3.14159, 2) == 3.14
        assert BaseCalculator.round(3.5) == 4
        assert BaseCalculator.round(3.14159, 0) == 3

    def test_pow(self):
        """Test power operation."""
        assert BaseCalculator.pow(2, 3) == 8
        assert BaseCalculator.pow(5, 0) == 1
        assert BaseCalculator.pow(4, 0.5) == 2

    def test_sqrt(self):
        """Test square root operation."""
        assert BaseCalculator.sqrt(9) == 3
        assert BaseCalculator.sqrt(0) == 0
        assert BaseCalculator.sqrt(2) == pytest.approx(1.414, rel=1e-3)

        with pytest.raises(
            ValueError, match="Cannot calculate square root of negative number"
        ):
            BaseCalculator.sqrt(-1)

    def test_cbrt(self):
        """Test cube root operation."""
        assert BaseCalculator.cbrt(8) == pytest.approx(2)
        assert BaseCalculator.cbrt(-8) == pytest.approx(-2)
        assert BaseCalculator.cbrt(0) == 0

    def test_log(self):
        """Test logarithm operation."""
        assert BaseCalculator.log(100, 10) == 2
        assert BaseCalculator.log(8, 2) == 3

        with pytest.raises(ValueError, match="x must be positive"):
            BaseCalculator.log(-1, 10)

        with pytest.raises(
            ValueError, match="base must be positive and not equal to 1"
        ):
            BaseCalculator.log(10, 1)

    def test_ln(self):
        """Test natural logarithm operation."""
        assert BaseCalculator.ln(math.e) == pytest.approx(1)
        assert BaseCalculator.ln(1) == 0

        with pytest.raises(ValueError, match="x must be positive"):
            BaseCalculator.ln(-1)

    def test_exp(self):
        """Test exponential operation."""
        assert BaseCalculator.exp(0) == 1
        assert BaseCalculator.exp(1) == pytest.approx(math.e)

    def test_min(self):
        """Test minimum operation."""
        assert BaseCalculator.min([1, 2, 3]) == 1
        assert BaseCalculator.min([-1, 0, 1]) == -1

        with pytest.raises(ValueError, match="numbers list cannot be empty"):
            BaseCalculator.min([])

    def test_max(self):
        """Test maximum operation."""
        assert BaseCalculator.max([1, 2, 3]) == 3
        assert BaseCalculator.max([-1, 0, 1]) == 1

        with pytest.raises(ValueError, match="numbers list cannot be empty"):
            BaseCalculator.max([])

    def test_sum(self):
        """Test sum operation."""
        assert BaseCalculator.sum([1, 2, 3]) == 6
        assert BaseCalculator.sum([]) == 0
        assert BaseCalculator.sum([-1, 1]) == 0

    def test_average(self):
        """Test average operation."""
        assert BaseCalculator.average([1, 2, 3]) == 2
        assert BaseCalculator.average([0, 0, 0]) == 0

        with pytest.raises(ValueError, match="numbers list cannot be empty"):
            BaseCalculator.average([])

    def test_median(self):
        """Test median operation."""
        assert BaseCalculator.median([1, 2, 3]) == 2
        assert BaseCalculator.median([1, 2, 3, 4]) == 2.5
        assert BaseCalculator.median([5]) == 5

        with pytest.raises(ValueError, match="numbers list cannot be empty"):
            BaseCalculator.median([])

    def test_mode(self):
        """Test mode operation."""
        assert BaseCalculator.mode([1, 2, 2, 3]) == [2]
        assert set(BaseCalculator.mode([1, 1, 2, 2])) == {1, 2}
        assert BaseCalculator.mode([1]) == [1]

        with pytest.raises(ValueError, match="numbers list cannot be empty"):
            BaseCalculator.mode([])

    def test_standard_deviation(self):
        """Test standard deviation operation."""
        assert BaseCalculator.standard_deviation([1, 2, 3]) == pytest.approx(
            0.816, rel=1e-3
        )
        assert BaseCalculator.standard_deviation([5, 5, 5]) == 0

        with pytest.raises(ValueError, match="numbers list cannot be empty"):
            BaseCalculator.standard_deviation([])

    def test_factorial(self):
        """Test factorial operation."""
        assert BaseCalculator.factorial(0) == 1
        assert BaseCalculator.factorial(5) == 120
        assert BaseCalculator.factorial(1) == 1

        with pytest.raises(ValueError, match="n must be non-negative"):
            BaseCalculator.factorial(-1)

    def test_gcd(self):
        """Test greatest common divisor operation."""
        assert BaseCalculator.gcd(12, 8) == 4
        assert BaseCalculator.gcd(17, 13) == 1
        assert BaseCalculator.gcd(0, 5) == 5

    def test_lcm(self):
        """Test least common multiple operation."""
        assert BaseCalculator.lcm(12, 8) == 24
        assert BaseCalculator.lcm(17, 13) == 221
        assert BaseCalculator.lcm(0, 5) == 0

    def test_dist(self):
        """Test distance calculation."""
        assert BaseCalculator.dist([0, 0], [3, 4]) == 5
        assert BaseCalculator.dist([1, 1], [1, 1]) == 0
        assert BaseCalculator.dist([0, 0], [1, 1], "manhattan") == 2

        with pytest.raises(ValueError, match="Points must have same dimensions"):
            BaseCalculator.dist([1, 2], [1, 2, 3])

    def test_norm_euclidean(self):
        """Test Euclidean norm calculation."""
        assert BaseCalculator.norm_euclidean([3, 4]) == 5
        assert BaseCalculator.norm_euclidean([0, 0]) == 0

    def test_hypot(self):
        """Test hypotenuse calculation."""
        assert BaseCalculator.hypot(3, 4) == 5
        assert BaseCalculator.hypot(0, 0) == 0

    def test_simple_interest(self):
        """Test simple interest calculation."""
        assert BaseCalculator.simple_interest(1000, 0.05, 2) == 100
        assert BaseCalculator.simple_interest(0, 0.1, 1) == 0

    def test_compound_interest(self):
        """Test compound interest calculation."""
        result = BaseCalculator.compound_interest(1000, 0.05, 2, 1)
        assert result == pytest.approx(1102.5)


class TestCalculator:
    """Test cases for Calculator class."""

    def test_list_allowed_fns_without_help(self):
        """Test listing allowed functions without help."""
        result = Calculator.list_allowed_fns(with_help=False)
        assert isinstance(result, str)
        # Should be a JSON string of function names
        import json

        functions = json.loads(result)
        assert isinstance(functions, list)
        assert "add" in functions
        assert "sqrt" in functions

    def test_list_allowed_fns_with_help(self):
        """Test listing allowed functions with help."""
        result = Calculator.list_allowed_fns(with_help=True)
        assert isinstance(result, str)
        # Should be a JSON string of function names with descriptions
        import json

        functions = json.loads(result)
        assert isinstance(functions, dict)
        assert "add" in functions
        assert isinstance(functions["add"], str)

    def test_help_valid_function(self):
        """Test help for valid function."""
        help_text = Calculator.help("add")
        assert "function: add" in help_text
        assert "Adds two numbers" in help_text

    def test_help_invalid_function(self):
        """Test help for invalid function."""
        with pytest.raises(
            ValueError, match="Function 'invalid_func' is not recognized"
        ):
            Calculator.help("invalid_func")

    def test_evaluate_basic_arithmetic(self):
        """Test evaluation of basic arithmetic expressions."""
        assert Calculator.evaluate("2 + 3") == 5
        assert Calculator.evaluate("10 - 4") == 6
        assert Calculator.evaluate("3 * 4") == 12
        assert Calculator.evaluate("15 / 3") == 5

    def test_evaluate_function_calls(self):
        """Test evaluation of function calls."""
        assert Calculator.evaluate("add(2, 3)") == 5
        assert Calculator.evaluate("sqrt(16)") == 4
        assert Calculator.evaluate("pow(2, 3)") == 8

    def test_evaluate_complex_expressions(self):
        """Test evaluation of complex expressions."""
        assert Calculator.evaluate("add(2, 3) * pow(2, 2)") == 20
        assert Calculator.evaluate("sqrt(16) + 2 * 3") == 10

    def test_evaluate_invalid_expression(self):
        """Test evaluation of invalid expressions."""
        with pytest.raises(ValueError, match="Invalid expression"):
            Calculator.evaluate("invalid_function(1, 2)")

        with pytest.raises(ValueError, match="Invalid expression"):
            Calculator.evaluate("2 +")
