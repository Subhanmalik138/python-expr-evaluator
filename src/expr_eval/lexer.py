"""Lexer: turn source text into a flat list of tokens.

Token kinds: NUMBER (float), IDENT (variable / function name), OP
(``+ - * / % ^ =``), LPAREN, RPAREN, COMMA, EOF. Whitespace is skipped.
Any other character raises :class:`LexError` with its position.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum, auto

from .errors import LexError

_NUMBER_RE = re.compile(r"(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?")
_IDENT_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
_SINGLE_CHAR_OPS = set("+-*/%^=,()")


class TokenKind(Enum):
    NUMBER = auto()
    IDENT = auto()
    OP = auto()
    LPAREN = auto()
    RPAREN = auto()
    COMMA = auto()
    EOF = auto()


@dataclass(frozen=True)
class Token:
    kind: TokenKind
    value: str
    position: int

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"Token({self.kind.name}, {self.value!r}, pos={self.position})"


def tokenize(source: str) -> list[Token]:
    """Split *source* into tokens. Raises :class:`LexError` on bad input."""
    tokens: list[Token] = []
    i = 0
    while i < len(source):
        ch = source[i]
        if ch.isspace():
            i += 1
            continue
        if ch.isdigit() or (ch == "." and i + 1 < len(source) and source[i + 1].isdigit()):
            match = _NUMBER_RE.match(source, i)
            assert match is not None  # guarded by the check above
            tokens.append(Token(TokenKind.NUMBER, match.group(0), i))
            i = match.end()
            continue
        if ch.isalpha() or ch == "_":
            match = _IDENT_RE.match(source, i)
            assert match is not None
            tokens.append(Token(TokenKind.IDENT, match.group(0), i))
            i = match.end()
            continue
        if ch in _SINGLE_CHAR_OPS:
            kind = {
                "(": TokenKind.LPAREN,
                ")": TokenKind.RPAREN,
                ",": TokenKind.COMMA,
            }.get(ch, TokenKind.OP)
            tokens.append(Token(kind, ch, i))
            i += 1
            continue
        raise LexError(f"Unexpected character {ch!r}", position=i)
    tokens.append(Token(TokenKind.EOF, "", len(source)))
    return tokens
