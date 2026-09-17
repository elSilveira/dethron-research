"""Audit the complete four-mode experiment from raw generations."""
import math
import re

from comparison_inputs import MODES, plan
from document_dataset import dataset
from document_oracle import grade, resolve


def summarize(records):
    expected_plan = plan()
    if len(records) != len(expected_plan):
        raise ValueError("Incomplete or duplicated execution")
    cases = {case["id"]: case for case in dataset()["cases"]}
    modes = {mode: dict(cases=0, answer_correct=0, supported_correct=0,
                       supported_accepted=0, valid_abstention=0, format_failures=0,
                       truncated=0, execution_errors=0, observed_tokens=0,
                       observed_seconds=0.0) for mode in MODES}
    assessments = []
    for row, expected in zip(records, expected_plan):
        if any(row.get(key) != value for key, value in expected.items()):
            raise ValueError("Altered inputs, mode, or execution order")
        totals = modes[row["mode"]]
        totals["cases"] += 1
        if "error" in row:
            if "response" in row or not isinstance(row["error"], str) or not row["error"]:
                raise ValueError("Ambiguous execution failure")
            totals["execution_errors"] += 1
            continue
        response = row["response"]
        if len(response["outputs"]) != 1:
            raise ValueError("Expected one output")
        output = response["outputs"][0]
        for key, limit in (("input_tokens", 1024), ("generated_tokens", 256)):
            if type(output[key]) is not int or not 1 <= output[key] <= limit:
                raise ValueError("Invalid token count")
        ids = output["token_ids"]
        if len(ids) != output["generated_tokens"] or any(type(t) is not int or t < 0 for t in ids):
            raise ValueError("Invalid token IDs")
        if (type(response["evaluated_tokens"]) is not int or
                response["evaluated_tokens"] != output["input_tokens"] + len(ids)):
            raise ValueError("Inconsistent evaluated tokens")
        seconds = response["seconds"]
        if type(seconds) not in (int, float) or not math.isfinite(seconds) or seconds < 0:
            raise ValueError("Invalid model time")
        if not isinstance(output["text"], str) or output["finish_reason"] not in ("eos", "length"):
            raise ValueError("Malformed output")
        case = cases[row["case_id"]]
        reference = resolve(case)
        if (reference["conclusion"] or "UNKNOWN") != case["expected"]:
            raise ValueError("Reference disagrees with frozen label")
        assessment = grade(output, reference)
        shown = set(re.findall(r"^\[(S\d+)\]", row["evidence"], re.MULTILINE))
        assessment["accepted"] &= set(assessment["citations"]) <= shown
        correct = (assessment["format_ok"] and assessment["answer"] == case["expected"]
                   and output["finish_reason"] == "eos")
        totals["answer_correct"] += correct
        totals["supported_correct"] += correct and case["expected"] != "UNKNOWN"
        totals["supported_accepted"] += assessment["accepted"]
        totals["valid_abstention"] += assessment["valid_abstention"]
        totals["format_failures"] += not assessment["format_ok"]
        totals["truncated"] += output["finish_reason"] == "length"
        totals["observed_tokens"] += response["evaluated_tokens"]
        totals["observed_seconds"] += seconds
        assessments.append(dict(case_id=row["case_id"], mode=row["mode"], **assessment))
    for totals in modes.values():
        totals["total_evaluated_tokens"] = None if totals["execution_errors"] else totals["observed_tokens"]
        useful = totals["supported_accepted"] + totals["valid_abstention"]
        totals["verified_useful"] = useful
        totals["tokens_per_verified_useful"] = (
            totals["observed_tokens"] / useful if useful and not totals["execution_errors"] else None)
    return {"scope": "development_diagnostic", "cases": len(cases),
            "supported_cases": 5, "unanswerable_cases": 3, "always_unknown_correct": 3,
            "modes": modes, "assessments": assessments,
            "limits": "Reference-based scoring, not an independent deployed guard or remote attestation; manual annotation cost unmeasured"}
