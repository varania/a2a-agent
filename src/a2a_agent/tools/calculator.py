"""A safe arithmetic calculator tool (no ``eval``)."""

from __future__ import annotations

import ast
import operator
from typing import Any

from langchain_core.tools import tool

_BINARY_OPERATORS: dict[type[ast.operator], Any] = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}

_UNARY_OPERATORS: dict[type[ast.unaryop], Any] = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}

_MAX_EXPRESSION_LENGTH = 200
_MAX_POWER = 100


def _evaluate(node: ast.AST) -> float | int:
    if isinstance(node, ast.Constant):
        if isinstance(node.value, bool) or not isinstance(node.value, int | float):
            raise ValueError("Only numeric literals are allowed.")
        return node.value
    if isinstance(node, ast.BinOp):
        operator_fn = _BINARY_OPERATORS.get(type(node.op))
        if operator_fn is None:
            raise ValueError(f"Unsupported operator: {type(node.op).__name__}")
        left, right = _evaluate(node.left), _evaluate(node.right)
        if isinstance(node.op, ast.Pow) and abs(right) > _MAX_POWER:
            raise ValueError(f"Exponent too large (max {_MAX_POWER}).")
        return operator_fn(left, right)
    if isinstance(node, ast.UnaryOp):
        operator_fn = _UNARY_OPERATORS.get(type(node.op))
        if operator_fn is None:
            raise ValueError(f"Unsupported operator: {type(node.op).__name__}")
        return operator_fn(_evaluate(node.operand))
    raise ValueError(f"Unsupported expression: {type(node).__name__}")


@tool
def calculator(expression: str) -> str:
    """Evaluate a basic arithmetic expression.

    Use this tool whenever the user asks for a numeric calculation that must be
    exact (sums, percentages, powers, integer division, ...).

    Args:
        expression: Arithmetic expression using numbers, parentheses and the
            operators +, -, *, /, //, %, **. Example: "(120 * 3) / 4".
    """
    if len(expression) > _MAX_EXPRESSION_LENGTH:
        return "Error: expression is too long."
    try:
        tree = ast.parse(expression, mode="eval")
        return str(_evaluate(tree.body))
    except (SyntaxError, TypeError, ValueError, ZeroDivisionError) as exc:
        return f"Error: {exc}"
