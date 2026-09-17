import pytest

from probes.capability.arithmetic import score_arithmetic


@pytest.mark.parametrize(
    "left,operation,right,response,expected",
    [
        (2, "+", 2, "4", 4),
        (2, "+", 3, "5", 5),
        (-8, "-", -3, "-5", -5),
        (-7, "*", 6, "-42", -42),
        (0, "*", 99, "0", 0),
        (12345678901234567890, "+", 1, "12345678901234567891", 12345678901234567891),
        (2, "+", 2, " \n+4\t", 4),
    ],
)
def test_scores_correct_integer_answers(left, operation, right, response, expected):
    result = score_arithmetic(left, operation, right, response)
    assert result.status == "PASS"
    assert result.expected == expected
    assert result.observed == expected
    assert result.reason == "correct"


def test_constant_four_fails_when_operands_change():
    assert score_arithmetic(2, "+", 2, "4").status == "PASS"
    result = score_arithmetic(2, "+", 3, "4")
    assert result.status == "FAIL"
    assert result.expected == 5
    assert result.observed == 4
    assert result.reason == "incorrect_result"


@pytest.mark.parametrize("response", [
    "", " ", "4 or 5", "4\n5", "2 + 2 = 4", "The answer is 4",
    "4 but also 5", "4.0", "4e0", "４", "٤", "True", "--4",
    "4\x00", "__import__('os').getcwd()",
])
def test_rejects_missing_ambiguous_or_out_of_contract_answers(response):
    result = score_arithmetic(2, "+", 2, response)
    assert result.status == "FAIL"
    assert result.observed is None
    assert result.reason == "invalid_response_format"


@pytest.mark.parametrize("left,operation,right,error", [
    (True, "+", 2, TypeError),
    (2, "+", False, TypeError),
    (2.0, "+", 2, TypeError),
    (2, "+", "2", TypeError),
    (2, "/", 2, ValueError),
    (2, "**", 2, ValueError),
])
def test_invalid_evaluator_inputs_raise_instead_of_scoring(left, operation, right, error):
    with pytest.raises(error):
        score_arithmetic(left, operation, right, "4")


@pytest.mark.parametrize("response", [None, 4, True, {"answer": 4}])
def test_non_text_candidate_outputs_fail(response):
    result = score_arithmetic(2, "+", 2, response)
    assert result.status == "FAIL"
    assert result.reason == "invalid_response_format"


def test_overlong_response_fails_without_integer_conversion_error():
    result = score_arithmetic(2, "+", 2, "4" * 5000)
    assert result.status == "FAIL"
    assert result.reason == "invalid_response_format"
