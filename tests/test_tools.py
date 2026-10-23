"""Tests for the LangChain tools."""

from __future__ import annotations

import pytest

from a2a_agent.tools import calculator, get_current_time


@pytest.mark.parametrize(
    ("expression", "expected"),
    [
        ("(120 * 3) / 4", "90.0"),
        ("2 + 3 * 4", "14"),
        ("7 // 2", "3"),
        ("2 ** 10", "1024"),
        ("-(4 + 1)", "-5"),
    ],
)
def test_calculator_evaluates_arithmetic(expression: str, expected: str) -> None:
    assert calculator.invoke(expression) == expected


@pytest.mark.parametrize(
    "expression",
    [
        "__import__('os').system('echo pwned')",
        "open('/etc/passwd').read()",
        "2 ** 1000",
        "1 / 0",
    ],
)
def test_calculator_rejects_dangerous_or_invalid_input(expression: str) -> None:
    assert calculator.invoke(expression).startswith("Error:")


def test_current_time_uses_requested_timezone() -> None:
    assert "Europe/Madrid" in get_current_time.invoke("Europe/Madrid")


def test_current_time_falls_back_to_utc_on_unknown_zone() -> None:
    assert "UTC" in get_current_time.invoke("Mars/Olympus_Mons")
