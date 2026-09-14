"""Reject inconsistent evidence before computing a document scoreboard."""
import math
from document_dataset import dataset
from document_oracle import resolve, grade, inputs


def require(condition, message):
    if not condition:
        raise ValueError(message)


def audit(events):
    try:
        return _audit(events)
    except (KeyError, TypeError, IndexError, StopIteration, AttributeError) as error:
        raise ValueError("Malformed document evidence") from error


def _audit(events):
    require(bool(events) and events[-1].get("kind") == "complete", "Incomplete document run")
    require(sum(e.get("kind") == "complete" for e in events) == 1, "Duplicate completion")
    documents = [e["data"] for e in events if e.get("kind") == "document"]
    workers = [e["data"] for e in events if e.get("kind") == "worker"]
    rows = [e["data"] for e in events if e.get("kind") == "case"]
    require(len(documents) == 1 and documents[0] == dataset(), "Document differs from frozen dataset")
    require(len(workers) == 1 and workers[0]["handshake"]["data"]["simulated"] is False,
            "Missing real worker identity")
    cases = documents[0]["cases"]
    require([r["id"] for r in rows] == [c["id"] for c in cases], "Missing, duplicate or reordered cases")
    for row, case in zip(rows, cases):
        for field in ("question", "expected", "document", "routes", "removed"):
            require(row[field] == case[field], f"Changed case {field}")
        reference = resolve(case)
        excerpt, requests = inputs(case)
        require(row["selected_text"] == excerpt, "Changed selected evidence")
        for field in ("state", "conclusion", "source_ids"):
            require(row["dna"][field] == reference[field], f"DNA reference disagrees: {field}")
        require(row["dna_correct"] is ((reference["conclusion"] or "UNKNOWN") == case["expected"]),
                "Inconsistent DNA score")
        modes = row["modes"]
        require(len(modes) == 2 and sorted(m["mode"] for m in modes) == ["full", "selected"],
                "Expected exactly one execution per mode")
        for result in modes:
            require(result["request"] == requests[result["mode"]], "Changed prompt or generation controls")
            data = result["response"]["data"]
            require(len(data["outputs"]) == 1, "Expected one generation")
            output = data["outputs"][0]
            require(isinstance(output["text"], str) and output["finish_reason"] in ("eos", "length"),
                    "Invalid generation output")
            input_count, generated, tokens = output["input_tokens"], output["generated_tokens"], output["token_ids"]
            require(type(input_count) is int and 1 <= input_count <= 1024 and type(generated) is int
                    and 1 <= generated <= 256, "Generation bounds violated")
            require(isinstance(tokens, list) and len(tokens) == generated
                    and all(type(t) is int and t >= 0 for t in tokens), "Inconsistent generated tokens")
            require(type(data["evaluated_tokens"]) is int and data["evaluated_tokens"] == input_count + generated,
                    "Inconsistent token accounting")
            seconds = result["seconds"]
            require(type(seconds) in (int, float) and math.isfinite(seconds) and seconds >= 0,
                    "Invalid timing measurement")
            assessment = grade(output, reference)
            for field, value in assessment.items():
                claimed = result["assessment"][field]
                require(type(claimed) is type(value) and claimed == value, f"Inconsistent assessment: {field}")
            correct = assessment["format_ok"] and assessment["answer"] == case["expected"] and output["finish_reason"] == "eos"
            require(result["answer_correct"] is correct, "Inconsistent answer score")
    return cases, rows
