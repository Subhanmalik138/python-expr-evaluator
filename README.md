# expr-eval

A small arithmetic expression evaluator in pure Python — no dependencies.
It lexes source text into tokens, parses them with the shunting-yard
algorithm into an AST, and evaluates the tree against an environment of
variables. It ships with a REPL and a CLI that can evaluate expressions
or whole script files.

```console
$ python -m expr_eval "2 + 3 * 4"
14
$ python -m expr_eval "x = 5" "x ^ 2"
5
25
$ python -m expr_eval -i
expr> 2 * pi * 3
18.84955592153876
```

## Features

- Operators `+ - * / % ^` (`^` is right-associative), parentheses, unary minus
- Variables and assignment — `x = 2 + 3`, then `x * 2`
- Function calls: `sqrt`, `sin`, `cos`, `tan`, `asin`, `acos`, `atan`,
  `log`, `log10`, `exp`, `abs`, `floor`, `ceil`, `min`, `max`, `pow`
- Constants `pi` and `e`
- Script files: one expression per line, `#` comments, state carries
  across lines
- Errors carry the source column, e.g. `Unexpected character '@' (at column 3)`

## Design decisions

1. **Two-pass parsing.** Shunting-yard first produces reverse Polish
   notation, then a stack machine builds the AST. Precedence lives in
   one small table (`parser._OPERATORS`), so adding an operator means
   adding one row — not restructuring a recursive-descent grammar.
2. **The AST is the interface.** Lexer, parser, and evaluator are
   separate modules joined only by the AST node types, so each can be
   tested in isolation (and a future code generator could consume the
   same tree).
3. **Explicit unary minus.** The parser rewrites a unary `-` to a
   distinct `u-` operator with its own precedence, which is what makes
   `-2 ^ 2` evaluate as `(-2) ^ 2` instead of a parse error.
4. **No dependencies, stdlib only.** `math` and `operator` cover the
   whole feature set, so the package installs anywhere Python 3.10+
   runs.

## How to run

Requires Python 3.10+.

```console
pip install -e .          # optional; exposes the `expr-eval` command
python -m expr_eval "sqrt(16) + max(1, 5)"
python -m expr_eval --vars x=2 --vars y=3 "x * y"
python -m expr_eval script.txt
python -m expr_eval -i    # REPL
```

A script file is one expression per line; `#` starts a comment and
assignments persist across lines:

```
# circle.txt
r = 3
2 * pi * r
```

## How to run tests

```console
python -m pytest
```

43 tests cover the lexer, parser (including precedence, associativity,
and malformed input), evaluator (functions, variables, error paths),
and the CLI/REPL.

## Project structure

```
src/expr_eval/
    __init__.py    public API (evaluate, parse, tokenize, ...)
    errors.py      LexError / ParseError / EvalError with source positions
    lexer.py       source text -> tokens
    parser.py      shunting-yard -> AST (Number, Variable, BinaryOp, ...)
    evaluator.py   AST -> value; Environment with pi/e and built-ins
    __main__.py    REPL + CLI
tests/             pytest suite (lexer, parser, evaluator, CLI)
```

## License

MIT — see [LICENSE](LICENSE).
