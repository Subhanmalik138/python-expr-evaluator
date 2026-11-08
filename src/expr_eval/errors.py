"""Error types for expr_eval.

Every error carries the source position where the problem was found, so
callers (the CLI, the REPL) can point at the offending character.
"""


class ExprError(Exception):
    """Base class for all expression errors."""

    def __init__(self, message: str, position: int | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.position = position

    def __str__(self) -> str:
        if self.position is None:
            return self.message
        return f"{self.message} (at column {self.position + 1})"


class LexError(ExprError):
    """Raised when the input contains a character the lexer cannot tokenize."""


class ParseError(ExprError):
    """Raised when the token stream is not a well-formed expression."""


class EvalError(ExprError):
    """Raised while evaluating a parsed expression (unknown name,
    division by zero, wrong argument count, ...)."""
