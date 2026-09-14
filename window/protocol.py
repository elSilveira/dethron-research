"""Validate the adapter's bounded public JSON-lines protocol."""
import json
import math

KINDS = {"started", "parent_created", "learned", "evolution", "task",
         "child_created", "checkpoint", "restored", "audit_verified", "encoding", "completed"}


def decode_event(line, sequence):
    event = json.loads(line)
    if not isinstance(event, dict) or sequence >= 150:
        raise ValueError("Invalid event or event limit exceeded")
    if (type(event.get("schema")) is not int or event["schema"] != 1
            or type(event.get("sequence")) is not int or event["sequence"] != sequence):
        raise ValueError("Unexpected event schema or sequence")
    if (not isinstance(event.get("kind"), str) or event["kind"] not in KINDS
            or not isinstance(event.get("data"), dict)):
        raise ValueError("Invalid event kind or data")
    if sequence == 0 and event["kind"] != "started":
        raise ValueError("Stream must begin with started")
    elapsed = event.get("elapsed_ms")
    if type(elapsed) not in (int, float) or not math.isfinite(elapsed) or elapsed < 0:
        raise ValueError("Invalid event clock")
    return event


def checked_report(report):
    if any(report.get(key) is not True for key in ("correct", "child_recalled", "audit_verified")):
        raise ValueError("Probe verification did not pass")
    if not isinstance(report.get("encoding"), dict) or report["encoding"].get("roundtrip") is not True:
        raise ValueError("Encoding verification did not pass")
    return report
