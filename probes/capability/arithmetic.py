"""Independent scoring for controlled integer arithmetic tasks."""

from dataclasses import dataclass
import operator
import re
from typing import Literal


MAX_RESPONSE_CHARS = 1024
OPERATIONS = {"+": operator.add, "-": operator.sub, "*": operator.mul}
INTEGER = re.compile(r"[+-]?[0-9]+")


@dataclass(frozen=True)
class ArithmeticScore:
    status: Literal["PASS", "FAIL"]
    expected: int
    observed: int | None
    reason: str


def score_arithmetic(
    left: int, operation: str, right: int, response: object
) -> ArithmeticScore:
    """Score one integer-only response; expected answers never come from candidates.

    Invalid task configuration raises; malformed candidate output receives FAIL.
    This controlled format intentionally excludes prose and expressions.
    """
    if type(left) is not int or type(right) is not int:
        raise TypeError("Operands must be integers, excluding booleans")
    if not isinstance(operation, str) or operation not in OPERATIONS:
        raise ValueError("Supported operations are +, -, and *")
    expected = OPERATIONS[operation](left, right)
    if not isinstance(response, str) or len(response) > MAX_RESPONSE_CHARS:
        return ArithmeticScore("FAIL", expected, None, "invalid_response_format")
    normalized = response.strip()
    if INTEGER.fullmatch(normalized) is None:
        return ArithmeticScore("FAIL", expected, None, "invalid_response_format")
    observed = int(normalized)
    if observed != expected:
        return ArithmeticScore("FAIL", expected, observed, "incorrect_result")
    return ArithmeticScore("PASS", expected, observed, "correct")
