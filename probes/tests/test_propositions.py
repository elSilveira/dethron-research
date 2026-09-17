import pytest

from probes.capability.propositions import score_semantics


@pytest.mark.parametrize("reference,response", [
    ("The sky is dark", "Dark is the sky"),
    ("The sky is dark", "  DARK   is the SKY. "),
    ("The sky is not dark", "Not dark is the sky"),
    ("The sky was dark", "Dark was the sky"),
    ("The door is open", "Open is the door"),
    ("All lights are off", "Off are all lights"),
    ("Some lights were not on", "Not on were some lights"),
    ("Alice follows Bob", "Bob is followed by Alice"),
    ("Alice does not follow Bob", "Bob is not followed by Alice"),
    ("Bob followed Alice", "Alice was followed by Bob"),
    ("Bob did not follow Alice", "Alice was not followed by Bob"),
])
def test_accepts_controlled_paraphrases(reference, response):
    result = score_semantics(reference, response)
    assert result.status == "PASS"
    assert result.reason == "equivalent"
    assert result.differences == ()


@pytest.mark.parametrize("reference,response,dimension", [
    ("The sky is dark", "The sky is not dark", "negated"),
    ("The sky is dark", "The sky was dark", "tense"),
    ("The sky is dark", "The sky is bright", "predicate"),
    ("The door is open", "The light is open", "subject"),
    ("All lights are off", "Some lights are off", "quantifier"),
    ("Alice follows Bob", "Bob follows Alice", "subject"),
    ("Alice follows Bob", "Alice follows Carol", "object"),
    ("Alice follows Bob", "Bob is not followed by Alice", "negated"),
    ("Alice follows Bob", "Bob was followed by Alice", "tense"),
])
def test_rejects_meaning_changes(reference, response, dimension):
    result = score_semantics(reference, response)
    assert result.status == "FAIL"
    assert result.reason == "meaning_changed"
    assert dimension in result.differences


@pytest.mark.parametrize("response", [
    "The heavens look gloomy", "It is dark", "The sky might be dark",
    "The sky is dark and bright", "The sky is dark. The door is open.",
    "The sky is dark?", "The sky is dark because it is night",
    "Not all lights are off", "", None, 4, "dark " * 1000,
])
def test_unknown_or_ambiguous_response_needs_review(response):
    result = score_semantics("The sky is dark", response)
    assert result.status == "INCONCLUSIVE"
    assert result.reason == "unsupported_response"


def test_unknown_reference_is_not_validated_by_matching_text():
    result = score_semantics("It is dark", "It is dark")
    assert result.status == "INCONCLUSIVE"
    assert result.reason == "unsupported_reference"


def test_word_overlap_does_not_erase_roles():
    left, right = "Alice follows Bob", "Bob follows Alice"
    assert sorted(left.split()) == sorted(right.split())
    assert score_semantics(left, right).status == "FAIL"
