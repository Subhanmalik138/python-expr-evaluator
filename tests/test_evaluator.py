import math

import pytest

from expr_eval.errors import EvalError
from expr_eval.evaluator import Environment, evaluate


def test_basic_arithmetic():
    assert evaluate("2 + 3 * 4") == 14
    assert evaluate("(2 + 3) * 4") == 20
    assert evaluate("10 % 3") == 1
    assert evaluate("7 / 2") == 3.5


def test_power_right_associative():
    assert evaluate("2 ^ 3 ^ 2") == 512  # 2^(3^2), not (2^3)^2


def test_unary_minus():
    assert evaluate("-5 + 3") == -2
    assert evaluate("-(2 + 3)") == -5
    assert evaluate("--5") == 5


def test_variables_and_assignment_persist():
    env = Environment()
    assert evaluate("x = 2 + 3", env) == 5
    assert evaluate("x * 2", env) == 10
    assert evaluate("x = x + 1", env) == 6


def test_builtin_constants():
    assert evaluate("pi") == pytest.approx(math.pi)
    assert evaluate("e") == pytest.approx(math.e)


def test_builtin_functions():
    assert evaluate("sqrt(16)") == 4
    assert evaluate("sin(0)") == 0
    assert evaluate("log(e)") == pytest.approx(1.0)
    assert evaluate("max(1, 9, 3)") == 9
    assert evaluate("min(1, 9, 3)") == 1
    assert evaluate("abs(0 - 7)") == 7
    assert evaluate("floor(2.9) + ceil(2.1)") == 5


def test_nested_calls_and_variables():
    env = Environment({"r": 3})
    assert evaluate("2 * pi * r", env) == pytest.approx(2 * math.pi * 3)


def test_division_by_zero():
    with pytest.raises(EvalError, match="Division by zero"):
        evaluate("1 / 0")


def test_undefined_variable():
    with pytest.raises(EvalError, match="Undefined variable"):
        evaluate("nope + 1")


def test_unknown_function():
    with pytest.raises(EvalError, match="Unknown function"):
        evaluate("frobnicate(1)")


def test_wrong_argument_count():
    with pytest.raises(EvalError):
        evaluate("sqrt(1, 2)")
    with pytest.raises(EvalError):
        evaluate("sqrt()")


def test_domain_error():
    with pytest.raises(EvalError):
        evaluate("sqrt(0 - 1)")


def test_scientific_notation():
    assert evaluate("1e3 + 2.5e-1") == pytest.approx(1000.25)
