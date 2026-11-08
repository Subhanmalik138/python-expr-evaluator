"""Parser: shunting-yard algorithm turning a token stream into an AST.

Grammar (informal)::

    statement := IDENT "=" expression | expression
    expression := term (("+" | "-") term)*
    term       := factor (("*" | "/" | "%") factor)*
    factor     := unary ("^" factor)?          # ^ is right-associative
    unary      := "-" unary | primary
    primary    := NUMBER | IDENT | IDENT "(" args ")" | "(" expression ")"
    args       := expression ("," expression)*

The parser works in two passes: shunting-yard produces reverse Polish
notation, then a stack machine builds the AST from it. Keeping the two
passes separate makes operator precedence a small table instead of a
tangle of recursive-descent methods, and makes unary minus and function
calls explicit tokens in the RPN stream.
"""

from __future__ import annotations

from dataclasses import dataclass

from .errors import ParseError
from .lexer import Token, TokenKind, tokenize

# operator -> (precedence, associativity)
# Higher precedence binds tighter. Unary minus is its own operator ("u-").
_OPERATORS: dict[str, tuple[int, str]] = {
    "+": (1, "left"),
    "-": (1, "left"),
    "*": (2, "left"),
    "/": (2, "left"),
    "%": (2, "left"),
    "^": (3, "right"),
    "u-": (4, "right"),
}


@dataclass(frozen=True)
class Number:
    value: float


@dataclass(frozen=True)
class Variable:
    name: str


@dataclass(frozen=True)
class BinaryOp:
    op: str
    left: "Node"
    right: "Node"


@dataclass(frozen=True)
class UnaryOp:
    op: str
    operand: "Node"


@dataclass(frozen=True)
class Call:
    name: str
    args: tuple["Node", ...]


@dataclass(frozen=True)
class Assign:
    name: str
    value: "Node"


Node = Number | Variable | BinaryOp | UnaryOp | Call | Assign


def parse(source: str) -> Node:
    """Parse *source* into an AST. Raises :class:`ParseError` on bad input."""
    tokens = tokenize(source)
    # Top level: a bare assignment "name = expr" is the only statement form.
    if (
        len(tokens) >= 3
        and tokens[0].kind == TokenKind.IDENT
        and tokens[1].kind == TokenKind.OP
        and tokens[1].value == "="
    ):
        value = _parse_expression(tokens[2:])
        return Assign(tokens[0].value, value)
    return _parse_expression(tokens)


def _parse_expression(tokens: list[Token]) -> Node:
    rpn = _shunting_yard(tokens)
    return _build_ast(rpn)


def _shunting_yard(tokens: list[Token]) -> list[Token]:
    """Convert the token stream to reverse Polish notation.

    Function calls are emitted as a CALL token whose value is
    ``"name/arity"`` (e.g. ``"max/2"``) so the AST builder knows how many
    operands to pop. Unary minus is emitted as the operator ``"u-"``.
    """
    output: list[Token] = []
    stack: list[Token] = []
    arg_counts: list[int] = []  # one entry per open function call
    prev: Token | None = None

    def is_unary_minus(tok: Token) -> bool:
        if tok.value != "-":
            return False
        # A minus is unary at the start, or after an operator, "(", or ",".
        return prev is None or prev.kind in (TokenKind.OP, TokenKind.LPAREN, TokenKind.COMMA)

    def pop_higher(op: Token) -> None:
        prec, assoc = _OPERATORS[op.value]
        while stack and stack[-1].kind == TokenKind.OP:
            top_prec, _ = _OPERATORS[stack[-1].value]
            if top_prec > prec or (top_prec == prec and assoc == "left"):
                output.append(stack.pop())
            else:
                break

    i = 0
    while i < len(tokens):
        tok = tokens[i]
        if tok.kind == TokenKind.EOF:
            break
        if tok.kind == TokenKind.NUMBER:
            output.append(tok)
        elif tok.kind == TokenKind.IDENT:
            # IDENT followed by "(" is a function call; otherwise a variable.
            nxt = tokens[i + 1] if i + 1 < len(tokens) else None
            if nxt is not None and nxt.kind == TokenKind.LPAREN:
                stack.append(tok)  # function name marker on the stack
                arg_counts.append(1)
            else:
                output.append(tok)
        elif tok.kind == TokenKind.LPAREN:
            stack.append(tok)
        elif tok.kind == TokenKind.RPAREN:
            while stack and stack[-1].kind != TokenKind.LPAREN:
                output.append(stack.pop())
            if not stack:
                raise ParseError("Mismatched ')'", position=tok.position)
            stack.pop()  # discard the "("
            if stack and stack[-1].kind == TokenKind.IDENT:
                # End of a function call: emit CALL with its arity.
                name = stack.pop().value
                arity = arg_counts.pop()
                if prev is not None and prev.kind == TokenKind.LPAREN:
                    arity = 0  # f() — no arguments at all
                output.append(Token(TokenKind.IDENT, f"{name}/{arity}", tok.position))
        elif tok.kind == TokenKind.COMMA:
            while stack and stack[-1].kind != TokenKind.LPAREN:
                output.append(stack.pop())
            if not stack:
                raise ParseError("Misplaced ','", position=tok.position)
            if arg_counts:
                arg_counts[-1] += 1
        elif tok.kind == TokenKind.OP:
            if tok.value == "=":
                raise ParseError(
                    "'=' is only allowed at the start of a statement",
                    position=tok.position,
                )
            op = Token(TokenKind.OP, "u-" if is_unary_minus(tok) else tok.value, tok.position)
            pop_higher(op)
            stack.append(op)
        prev = tok
        i += 1

    while stack:
        top = stack.pop()
        if top.kind == TokenKind.LPAREN:
            raise ParseError("Mismatched '('", position=top.position)
        if top.kind == TokenKind.IDENT:
            raise ParseError(f"Unclosed function call {top.value!r}", position=top.position)
        output.append(top)
    return output


def _build_ast(rpn: list[Token]) -> Node:
    """Build an AST from a reverse-Polish token list."""
    stack: list[Node] = []
    for tok in rpn:
        if tok.kind == TokenKind.NUMBER:
            stack.append(Number(float(tok.value)))
        elif tok.kind == TokenKind.IDENT:
            if "/" in tok.value:  # a CALL marker: "name/arity"
                name, arity_s = tok.value.rsplit("/", 1)
                arity = int(arity_s)
                if len(stack) < arity:
                    raise ParseError(
                        f"Not enough arguments for {name}()", position=tok.position
                    )
                args = tuple(stack[len(stack) - arity :]) if arity else ()
                del stack[len(stack) - arity :]
                stack.append(Call(name, args))
            else:
                stack.append(Variable(tok.value))
        elif tok.kind == TokenKind.OP:
            if tok.value == "u-":
                if not stack:
                    raise ParseError("Missing operand for unary '-'", position=tok.position)
                stack.append(UnaryOp("-", stack.pop()))
            else:
                if len(stack) < 2:
                    raise ParseError(
                        f"Missing operand for {tok.value!r}", position=tok.position
                    )
                right = stack.pop()
                left = stack.pop()
                stack.append(BinaryOp(tok.value, left, right))
        else:  # pragma: no cover - shunting-yard never emits these
            raise ParseError(f"Unexpected token {tok!r}", position=tok.position)
    if len(stack) != 1:
        raise ParseError("Could not parse expression: leftover operands")
    return stack[0]
