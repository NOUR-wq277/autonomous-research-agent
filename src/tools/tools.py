"""General tool utilities and helper tool definitions."""

from datetime import datetime
from typing import Any, Dict, Union


def get_current_datetime() -> str:
    """Return the current ISO formatted timestamp and human-readable date."""
    now = datetime.now()
    return now.strftime("%Y-%m-%d %H:%M:%S")


def perform_calculation(a: float, b: float, operation: str) -> Union[float, str]:
    """Execute standard arithmetic operations safely."""
    op = operation.lower().strip()
    if op in ("add", "+", "sum"):
        return a + b
    elif op in ("subtract", "-", "sub"):
        return a - b
    elif op in ("multiply", "*", "mul"):
        return a * b
    elif op in ("divide", "/", "div"):
        if b == 0:
            return "Error: Division by zero"
        return a / b
    return f"Error: Unknown operation '{operation}'"


TOOL_DEFINITIONS: Dict[str, Any] = {
    "get_current_datetime": {
        "function": get_current_datetime,
        "description": "Returns the current local date and time.",
    },
    "perform_calculation": {
        "function": perform_calculation,
        "description": "Performs arithmetic operations (add, subtract, multiply, divide).",
    },
}
