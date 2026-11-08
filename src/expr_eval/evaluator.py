"""Evaluator: walk an AST and compute its value.

An :class:`Environment` holds variables (pre-seeded with the constants
``pi`` and ``e``) plus a table of built-in functions. Assignment writes
into the environment, so a REPL or script file can build up state line
by line. Evaluation is deliberately side-effect free except for that
one assignment case.
"""

from __future__ import annotations

import math
import operator

from .errors import EvalError
from .parser import Assign, BinaryOp, Call, Node, Number, UnaryOp, Variable

_BINARY_OPS = {
    "+": operator.add,
    "-": operator.sub,
    "*": operator.mul,
    "/": operator.truediv,
    "%": operator.mod,
    "^": operator.pow,
}

_BUILTINS: dict[str, object] = {
    "sqrt": math.sqrt,
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "asin": math.asin,
    "acos": math.acos,
    "atan": math.atan,
    "log": math.log,
    "log10": math.log10,
    "exp": math.exp,
    "abs": abs,
    "floor": math.floor,
    "ceil": math.ceil,
    "min": min,
    "max": max,
    "pow": math.pow,
}


class Environment:
    """Variable store. Starts with the constants ``pi`` and ``e``."""

    def __init__(self, variables: dict[str, float] | None = None) -> None:
        self.variables: dict[str, float] = {"pi": math.pi, "e": math.e}
        if variables:
            self.variables.update(variables)

    def get(self, name: str, position: int | None = None) -> float:
        try:
            return self.variables[name]
        except KeyError:
            raise EvalError(f"Undefined variable {name!r}", position=position) from None

    def set(self, name: str, value: float) -> None:
        self.variables[name] = value

    def snapshot(self) -> dict[str, float]:
        return dict(self.variables)


class Evaluator:
    def __init__(self, env: Environment | None = None) -> None:
        self.env = env or Environment()

    def eval(self, node: Node) -> float:
        match node:
            case Number(value):
                return value
            case Variable(name):
                return self.env.get(name)
            case UnaryOp("-", operand):
                return -self.eval(operand)
            case BinaryOp(op, left, right):
                return self._binary(op, left, right)
            case Call(name, args):
                return self._call(name, args)
            case Assign(name, value):
                result = self.eval(value)
                self.env.set(name, result)
                return result
            case _:
                raise EvalError(f"Cannot evaluate node {node!r}")

    def _binary(self, op: str, left: Node, right: Node) -> float:
        func = _BINARY_OPS[op]
        l, r = self.eval(left), self.eval(right)
        try:
            return func(l, r)
        except ZeroDivisionError:
            raise EvalError("Division by zero") from None
        except (ValueError, OverflowError) as exc:
            raise EvalError(f"{op} failed: {exc}") from None

    def _call(self, name: str, args: tuple[Node, ...]) -> float:
        func = _BUILTINS.get(name)
        if func is None:
            raise EvalError(f"Unknown function {name!r}")
        values = [self.eval(arg) for arg in args]
        try:
            result = func(*values)  # type: ignore[operator]
        except TypeError:
            raise EvalError(
                f"{name}() called with {len(values)} argument(s)"
            ) from None
        except ValueError as exc:
            raise EvalError(f"{name}() failed: {exc}") from None
        return float(result)


def evaluate(source: str, env: Environment | None = None) -> float:
    """Parse *source* and evaluate it in *env* (a fresh one if omitted)."""
    from .parser import parse

    return Evaluator(env).eval(parse(source))
