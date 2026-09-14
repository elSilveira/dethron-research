"""Separate coverage, citation acceptance and abstention; preserve all failures."""
from document_audit import audit


def summarize(events):
    cases, rows = audit(events)
    summary = {"cases": len(rows), "dna_correct": sum(r["dna_correct"] for r in rows),
               "audit": "independent_raw_evidence_v1", "evaluation_scope": "development_diagnostic",
               "always_unknown_correct": sum(c["expected"] == "UNKNOWN" for c in cases)}
    for mode in ("full", "selected"):
        totals = dict(answer_correct=0, supported_correct=0, abstention_correct=0,
                      accepted=0, false_accepts=0, format_failures=0, truncated=0,
                      evaluated_tokens=0, seconds=0)
        for row, case in zip(rows, cases):
            if row["expected"] != case["expected"]:
                raise ValueError("Changed expected answer")
            result = next(m for m in row["modes"] if m["mode"] == mode)
            output = result["response"]["data"]["outputs"][0]
            a = result["assessment"]
            correct = a["format_ok"] and a["answer"] == case["expected"] and output["finish_reason"] == "eos"
            if result["answer_correct"] != correct:
                raise ValueError("Inconsistent answer score")
            totals["answer_correct"] += correct
            totals["supported_correct"] += correct and case["expected"] != "UNKNOWN"
            totals["abstention_correct"] += correct and case["expected"] == "UNKNOWN"
            totals["accepted"] += a["accepted"]
            totals["false_accepts"] += a["accepted"] and not correct
            totals["format_failures"] += not a["format_ok"]
            totals["truncated"] += output["finish_reason"] == "length"
            totals["evaluated_tokens"] += result["response"]["data"]["evaluated_tokens"]
            totals["seconds"] += result["seconds"]
        summary[mode] = totals
    return summary
