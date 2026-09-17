"""Controlled semantic equivalence; not a general language judge."""

from dataclasses import dataclass, fields
import re
from typing import Literal


@dataclass(frozen=True)
class Proposition:
    subject: str
    predicate: str
    object: str | None
    negated: bool
    tense: str
    quantifier: str


@dataclass(frozen=True)
class SemanticScore:
    status: Literal["PASS", "FAIL", "INCONCLUSIVE"]
    reason: str
    differences: tuple[str, ...] = ()
    expected: Proposition | None = None
    observed: Proposition | None = None


SUBJECT = r"(?P<subject>the (?:sky|door|light)|(?:all|some) lights)"
PROPERTY = r"(?P<negated>not )?(?P<predicate>dark|bright|open|closed|on|off)"
COPULA = r"(?P<copula>is|was|are|were)"
NAME = r"(?:alice|bob|carol)"
PROPERTY_PATTERNS = (
    re.compile(fr"{SUBJECT} {COPULA} {PROPERTY}"),
    re.compile(fr"{PROPERTY} {COPULA} {SUBJECT}"),
)
ACTIVE = re.compile(
    fr"(?P<subject>{NAME}) "
    r"(?P<verb>follows|followed|does not follow|did not follow) "
    fr"(?P<object>{NAME})"
)
PASSIVE = re.compile(
    fr"(?P<object>{NAME}) (?P<copula>is|was) "
    fr"(?P<negated>not )?followed by (?P<subject>{NAME})"
)


def _parse(text: object) -> Proposition | None:
    if not isinstance(text, str) or len(text) > 1024:
        return None
    text = " ".join(text.lower().split())
    if text.endswith("."):
        text = text[:-1]
    for pattern in PROPERTY_PATTERNS:
        match = pattern.fullmatch(text)
        if match is None:
            continue
        data = match.groupdict()
        quantifier, subject = data["subject"].split(" ", 1)
        plural = subject == "lights"
        if plural != (data["copula"] in {"are", "were"}):
            return None
        return Proposition(
            subject, data["predicate"], None, bool(data["negated"]),
            "past" if data["copula"] in {"was", "were"} else "present",
            quantifier,
        )
    match = ACTIVE.fullmatch(text)
    if match:
        data = match.groupdict()
        return Proposition(
            data["subject"], "follow", data["object"], "not" in data["verb"],
            "past" if data["verb"] in {"followed", "did not follow"} else "present",
            "named",
        )
    match = PASSIVE.fullmatch(text)
    if match:
        data = match.groupdict()
        return Proposition(
            data["subject"], "follow", data["object"], bool(data["negated"]),
            "past" if data["copula"] == "was" else "present", "named",
        )
    return None


def score_semantics(reference: object, response: object) -> SemanticScore:
    """Compare controlled assertions in a caller-established shared context.

    FAIL means not equivalent, not necessarily contradictory or factually false.
    Unknown grammar requires review, even when the two strings are identical.
    """
    expected = _parse(reference)
    if expected is None:
        return SemanticScore("INCONCLUSIVE", "unsupported_reference")
    observed = _parse(response)
    if observed is None:
        return SemanticScore("INCONCLUSIVE", "unsupported_response", expected=expected)
    differences = tuple(
        field.name for field in fields(Proposition)
        if getattr(expected, field.name) != getattr(observed, field.name)
    )
    return SemanticScore(
        "FAIL" if differences else "PASS",
        "meaning_changed" if differences else "equivalent",
        differences, expected, observed,
    )
