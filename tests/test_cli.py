import subprocess
import sys
import textwrap

import pytest

from expr_eval.__main__ import main


def run_cli(*args):
    return main(list(args))


def test_cli_single_expression(capsys):
    assert run_cli("2 + 3 * 4") == 0
    assert capsys.readouterr().out.strip() == "14"


def test_cli_integer_like_result_prints_without_decimal(capsys):
    assert run_cli("10 / 4") == 0
    assert capsys.readouterr().out.strip() == "2.5"
    assert run_cli("4 * 2") == 0
    assert capsys.readouterr().out.strip() == "8"


def test_cli_multiple_expressions_share_state(capsys):
    assert run_cli("x = 5", "x ^ 2") == 0
    assert capsys.readouterr().out.splitlines() == ["5", "25"]


def test_cli_error_sets_exit_code(capsys):
    assert run_cli("1 / 0") == 1
    assert "Division by zero" in capsys.readouterr().err


def test_cli_vars_flag(capsys):
    assert run_cli("--vars", "x=2", "--vars", "y=3", "x * y") == 0
    assert capsys.readouterr().out.strip() == "6"


def test_cli_script_file(tmp_path, capsys):
    script = tmp_path / "calc.txt"
    script.write_text(
        textwrap.dedent(
            """\
            # a comment line
            a = 10
            b = a * 2

            b + 1
            """
        ),
        encoding="utf-8",
    )
    assert run_cli(str(script)) == 0
    assert capsys.readouterr().out.splitlines() == [
        "a = 10 = 10",
        "b = a * 2 = 20",
        "b + 1 = 21",
    ]


def test_cli_script_file_error_continues(tmp_path, capsys):
    script = tmp_path / "bad.txt"
    script.write_text("1 / 0\n2 + 2\n", encoding="utf-8")
    assert run_cli(str(script)) == 1
    assert capsys.readouterr().out.strip() == "2 + 2 = 4"


def test_repl_evaluates_and_quits(monkeypatch, capsys):
    inputs = iter(["2 + 2", "vars", "exit"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))
    assert run_cli("-i") == 0
    out = capsys.readouterr().out
    assert "4" in out
    assert "pi" in out and "e" in out


def test_repl_error_does_not_crash(monkeypatch, capsys):
    inputs = iter(["1 / 0", "quit"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))
    assert run_cli("-i") == 0
    assert "Division by zero" in capsys.readouterr().out


def test_module_runs_as_script():
    proc = subprocess.run(
        [sys.executable, "-m", "expr_eval", "3 ^ 3"],
        capture_output=True, text=True, cwd="src",
    )
    assert proc.returncode == 0
    assert proc.stdout.strip() == "27"
