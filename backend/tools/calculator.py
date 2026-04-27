"""
MARS Tool — Safe Math Calculator.

Evaluates arithmetic expressions using Python's AST module.
No eval() — no arbitrary code execution risk.
Supports: +, -, *, /, //, %, **, unary minus, parentheses.
"""
import ast
import operator as op
import logging

logger = logging.getLogger(__name__)

# Allowed AST node types and operators
_ALLOWED_OPERATORS = {
    ast.Add:  op.add,
    ast.Sub:  op.sub,
    ast.Mult: op.mul,
    ast.Div:  op.truediv,
    ast.FloorDiv: op.floordiv,
    ast.Mod:  op.mod,
    ast.Pow:  op.pow,
    ast.USub: op.neg,
}


def _safe_eval(node):
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            return node.value
        raise ValueError(f"Unsupported literal: {node.value}")
    elif isinstance(node, ast.BinOp):
        fn = _ALLOWED_OPERATORS.get(type(node.op))
        if fn is None:
            raise ValueError(f"Operator not allowed: {type(node.op).__name__}")
        return fn(_safe_eval(node.left), _safe_eval(node.right))
    elif isinstance(node, ast.UnaryOp):
        fn = _ALLOWED_OPERATORS.get(type(node.op))
        if fn is None:
            raise ValueError(f"Unary operator not allowed: {type(node.op).__name__}")
        return fn(_safe_eval(node.operand))
    else:
        raise ValueError(f"Unsupported AST node: {type(node).__name__}")


def calculator(expression: str) -> str:
    """
    Safely evaluate a mathematical expression.

    Args:
        expression: A math expression string, e.g. "2 ** 10 + 3 * 4"

    Returns:
        Result as a string, or an error message.
    """
    try:
        tree = ast.parse(expression.strip(), mode="eval")
        result = _safe_eval(tree.body)
        # Format: avoid unnecessary trailing zeros
        if isinstance(result, float) and result.is_integer():
            result = int(result)
        return f"{expression} = {result}"
    except Exception as exc:
        logger.warning("calculator failed for '%s': %s", expression, exc)
        return f"Calculator error for '{expression}': {exc}"
