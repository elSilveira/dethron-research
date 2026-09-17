"""Post-process authenticated receiver artifacts; no sender status counts as completion."""
import base64
import hashlib
import json

from dethron_gateway.parts import validate
from dethron_gateway.protocol import data_envelope, receipt_envelope
from dethron_gateway.wire import authenticate


def audit_case(root):
    m = json.loads((root/"manifest.json").read_text())
    rows = [json.loads(line) for line in (root/"timeline.jsonl").read_text().splitlines()]
    stops = [r for r in rows if r["event"] == "crash" and r["node"] == "O"]
    fetches = [r for r in rows if r["event"] == "fetch_complete" and r["limit_kb"] == 64]
    if len(stops) != 1 or len(fetches) != 3 or stops[0]["time"] >= fetches[0]["time"]:
        raise ValueError("missing offline-origin or contact evidence")
    if [r["relay"] for r in fetches] != ["C", "A", "B"]:
        raise ValueError("contact schedule mismatch")
    for i, row in enumerate(fetches):
        state = row.get("receiver", {})
        complete = m["mode"] == "split" and i == 2
        if state.get("completed") is not complete:
            raise ValueError("completion does not match the constrained contact schedule")
        expected_objects = [] if m["mode"] == "whole" else [
            {"id": m["object"]["id"], "count": min(i+1, 2 if m["mode"] == "missing" else 3),
             "complete": complete}]
        if state.get("objects") != expected_objects:
            raise ValueError("unique parts do not match the constrained contact schedule")
    pieces, wholes = {}, []
    for path in (root/"D"/"packets").glob("*.lxmf"):
        obj = authenticate(path.read_bytes(), bytes.fromhex(m["source"]["public_key"]),
                           m["destination"]["destination"], m["expires"]-1)
        if obj not in m["inputs"].values():
            raise ValueError("receiver packet was not among declared source submissions")
        payload = base64.b64decode(obj["payload"], validate=True)
        if m["mode"] == "whole":
            wholes.append(payload)
        else:
            manifest, index, content = validate(payload)
            if manifest != m["object"] or (index in pieces and pieces[index] != content):
                raise ValueError("incompatible parts")
            pieces[index] = content
    output = root/"D"/"output.bin"
    receipt_path = root/"D"/"completion.lxmf"
    if m["mode"] == "missing":
        if set(pieces) != {0, 2} or output.exists() or receipt_path.exists():
            raise ValueError("missing-part control incorrectly completed")
        return {"audit": "passed", "unique_parts": 2, "completed": False}
    expected = hashlib.shake_256(b"dethron-g2-profile-v1").digest(m["profile"]["payload_bytes"])
    if m["mode"] == "split":
        if set(pieces) != {0, 1, 2} or b"".join(pieces[i] for i in range(3)) != expected:
            raise ValueError("received parts do not reconstruct the exact original")
    elif not wholes or any(content != expected for content in wholes):
        raise ValueError("whole-object positive control mismatch")
    if not output.exists() or output.read_bytes() != expected:
        raise ValueError("receiver output mismatch")
    receipt = authenticate(receipt_path.read_bytes(), bytes.fromhex(m["destination"]["public_key"]),
                           m["source"]["destination"], m["expires"]-1)
    obligation = data_envelope(m["source"]["destination"], m["destination"]["destination"], expected,
                               m["expires"], m["object"]["id"])
    if receipt != receipt_envelope(obligation):
        raise ValueError("local completion receipt does not match the whole object")
    return {"audit": "passed", "unique_parts": len(pieces), "completed": True,
            "sha256": hashlib.sha256(expected).hexdigest(), "receipt": "signed locally, not returned to offline origin"}
