"""REPL and CLI for expr_eval.

Usage::

    python -m expr_eval "2 + 3 * 4"     # print the result
    python -m expr_eval -i              # start the REPL
    python -m expr_eval script.txt      # evaluate one expression per line
    python -m expr_eval --vars x=2 y=3 "x * y"

In the REPL, ``vars`` lists defined variables, ``help`` shows a short
summary, and ``exit`` / ``quit`` (or Ctrl-D) leaves. Errors are printed
with their source position instead of a traceback.
"""

from __future__ import annotations

import argparse
import sys

from .errors import ExprError
from .evaluator import Environment, Evaluator
from .parser import parse

PROMPT = "expr> "
HELP_TEXT = """Commands:
  <expression>   evaluate it (assignments like x = 2 + 3 persist)
  vars           list defined variables
  help           show this text
  exit | quit    leave the REPL

Operators: + - * / % ^ (right-associative), parentheses, unary minus.
Functions: sqrt sin cos tan asin acos atan log log10 exp abs floor ceil min max pow
Constants: pi, e
"""


def _format(value: float) -> str:
    if value == int(value) and abs(value) < 1e15:
        return str(int(value))
    return repr(value)


def run_repl(evaluator: Evaluator) -> int:
    print("Expression evaluator — type 'help' for commands, 'exit' to quit.")
    while True:
        try:
            line = input(PROMPT)
        except (EOFError, KeyboardInterrupt):
            print()
            return 0
        stripped = line.strip()
        if not stripped:
            continue
        if stripped in ("exit", "quit"):
            return 0
        if stripped == "help":
            print(HELP_TEXT, end="")
            continue
        if stripped == "vars":
            for name, value in sorted(evaluator.env.snapshot().items()):
                print(f"  {name} = {_format(value)}")
            continue
        try:
            result = evaluator.eval(parse(stripped))
        except ExprError as exc:
            print(f"Error: {exc}")
            continue
        print(_format(result))
    return 0


def _parse_var_assignments(raw: list[str]) -> dict[str, float]:
    variables: dict[str, float] = {}
    for item in raw:
        if "=" not in item:
            raise ValueError(f"--vars entry {item!r} must look like name=value")
        name, _, value = item.partition("=")
        name = name.strip()
        if not name.isidentifier():
            raise ValueError(f"--vars entry {item!r} has an invalid name")
        try:
            variables[name] = float(value)
        except ValueError:
            raise ValueError(f"--vars entry {item!r} is not a number") from None
    return variables


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="expr_eval",
        description="Evaluate arithmetic expressions (see --help for the REPL).",
    )
    parser.add_argument("input", nargs="*", help="expression(s) or a .txt script file")
    parser.add_argument("-i", "--interactive", action="store_true", help="start the REPL")
    parser.add_argument(
        "--vars", action="append", default=[], metavar="NAME=VALUE",
        help="seed a variable; repeatable, e.g. --vars x=2 --vars y=3",
    )
    args = parser.parse_args(argv)

    try:
        variables = _parse_var_assignments(args.vars)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    evaluator = Evaluator(Environment(variables))

    if args.interactive or not args.input:
        return run_repl(evaluator)

    exit_code = 0
    for item in args.input:
        if item.endswith(".txt"):
            try:
                with open(item, encoding="utf-8") as fh:
                    lines = fh.readlines()
            except OSError as exc:
                print(f"Error: cannot read {item}: {exc}", file=sys.stderr)
                return 2
            for lineno, line in enumerate(lines, start=1):
                stripped = line.strip()
                if not stripped or stripped.startswith("#"):
                    continue
                try:
                    result = evaluator.eval(parse(stripped))
                except ExprError as exc:
                    print(f"{item}:{lineno}: Error: {exc}", file=sys.stderr)
                    exit_code = 1
                    continue
                print(f"{stripped} = {_format(result)}")
            continue
        try:
            result = evaluator.eval(parse(item))
        except ExprError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            exit_code = 1
            continue
        print(_format(result))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
