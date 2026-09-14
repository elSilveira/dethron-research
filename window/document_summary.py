"""Separate coverage, citation acceptance and abstention; preserve all failures."""
def summarize(events):
    if not events or events[-1].get("kind") != "complete":
        raise ValueError("Incomplete document run")
    documents = [e["data"] for e in events if e.get("kind") == "document"]
    workers = [e["data"] for e in events if e.get("kind") == "worker"]
    rows = [e["data"] for e in events if e.get("kind") == "case"]
    if len(documents) != 1 or len(workers) != 1 or workers[0]["handshake"]["data"]["simulated"] is not False:
        raise ValueError("Missing real model/document identity")
    cases = documents[0]["cases"]
    if len(rows) != 8 or [r["id"] for r in rows] != [c["id"] for c in cases]:
        raise ValueError("Missing document cases")
    summary = {"cases": len(rows), "dna_correct": sum(r["dna_correct"] for r in rows),
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
