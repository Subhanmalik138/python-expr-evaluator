import pytest

from expr_eval.errors import LexError
from expr_eval.lexer import TokenKind, tokenize


def kinds(source):
    return [(t.kind, t.value) for t in tokenize(source) if t.kind != TokenKind.EOF]


def test_numbers_and_identifiers():
    assert kinds("2 + x") == [
        (TokenKind.NUMBER, "2"),
        (TokenKind.OP, "+"),
        (TokenKind.IDENT, "x"),
    ]


def test_floats_and_scientific_notation():
    assert kinds("3.14 0.5 1e3 2.5e-2 .75") == [
        (TokenKind.NUMBER, "3.14"),
        (TokenKind.NUMBER, "0.5"),
        (TokenKind.NUMBER, "1e3"),
        (TokenKind.NUMBER, "2.5e-2"),
        (TokenKind.NUMBER, ".75"),
    ]


def test_parens_comma_and_assignment():
    assert kinds("f(a, b) = (1)") == [
        (TokenKind.IDENT, "f"),
        (TokenKind.LPAREN, "("),
        (TokenKind.IDENT, "a"),
        (TokenKind.COMMA, ","),
        (TokenKind.IDENT, "b"),
        (TokenKind.RPAREN, ")"),
        (TokenKind.OP, "="),
        (TokenKind.LPAREN, "("),
        (TokenKind.NUMBER, "1"),
        (TokenKind.RPAREN, ")"),
    ]


def test_whitespace_is_ignored():
    assert kinds("  1\t+\n2  ") == [
        (TokenKind.NUMBER, "1"),
        (TokenKind.OP, "+"),
        (TokenKind.NUMBER, "2"),
    ]


def test_unexpected_character_raises_with_position():
    with pytest.raises(LexError) as excinfo:
        tokenize("2 @ 3")
    assert excinfo.value.position == 2


def test_eof_token_is_last():
    tokens = tokenize("1")
    assert tokens[-1].kind == TokenKind.EOF
    assert tokens[-1].position == 1
