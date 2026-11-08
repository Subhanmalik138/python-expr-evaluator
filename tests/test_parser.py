import pytest

from expr_eval.errors import ParseError
from expr_eval.parser import Assign, BinaryOp, Call, Number, UnaryOp, Variable, parse


def test_precedence_mul_binds_tighter_than_add():
    assert parse("2 + 3 * 4") == BinaryOp(
        "+", Number(2.0), BinaryOp("*", Number(3.0), Number(4.0))
    )


def test_parentheses_override_precedence():
    assert parse("(2 + 3) * 4") == BinaryOp(
        "*", BinaryOp("+", Number(2.0), Number(3.0)), Number(4.0)
    )


def test_power_is_right_associative():
    assert parse("2 ^ 3 ^ 2") == BinaryOp(
        "^", Number(2.0), BinaryOp("^", Number(3.0), Number(2.0))
    )


def test_unary_minus_binds_tighter_than_power_base():
    assert parse("-2 ^ 2") == BinaryOp("^", UnaryOp("-", Number(2.0)), Number(2.0))


def test_double_unary_minus():
    assert parse("--5") == UnaryOp("-", UnaryOp("-", Number(5.0)))


def test_function_call_with_multiple_args():
    assert parse("max(1, 2 + 3)") == Call(
        "max", (Number(1.0), BinaryOp("+", Number(2.0), Number(3.0)))
    )


def test_nested_function_calls():
    assert parse("sqrt(max(1, 4))") == Call("sqrt", (Call("max", (Number(1.0), Number(4.0))),))


def test_assignment_statement():
    assert parse("x = 2 + 3") == Assign("x", BinaryOp("+", Number(2.0), Number(3.0)))


def test_bare_variable():
    assert parse("answer") == Variable("answer")


def test_mismatched_open_paren():
    with pytest.raises(ParseError):
        parse("(2 + 3")


def test_mismatched_close_paren():
    with pytest.raises(ParseError):
        parse("2 + 3)")


def test_missing_operand():
    with pytest.raises(ParseError):
        parse("2 +")


def test_equals_mid_expression_rejected():
    with pytest.raises(ParseError):
        parse("2 = 3")


def test_empty_input_rejected():
    with pytest.raises(ParseError):
        parse("")
