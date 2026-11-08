"""expr_eval — a small arithmetic expression evaluator.

Pipeline: source text -> lexer (tokens) -> parser (shunting-yard to an
AST) -> evaluator (walks the AST against an environment of variables).

Supports numbers, + - * / % ^ (right-associative), parentheses, unary
minus, variables, assignment (``x = 2 + 3``), and calls to a small set of
built-in math functions (``sqrt``, ``sin``, ``cos``, ``log``, ...).
"""

from .errors import ExprError, LexError, ParseError, EvalError
from .lexer import Token, TokenKind, tokenize
from .parser import parse
from .evaluator import Environment, Evaluator, evaluate

__all__ = [
    "ExprError",
    "LexError",
    "ParseError",
    "EvalError",
    "Token",
    "TokenKind",
    "tokenize",
    "parse",
    "Environment",
    "Evaluator",
    "evaluate",
]

__version__ = "1.0.0"
