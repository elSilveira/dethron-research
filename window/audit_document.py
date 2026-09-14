"""Re-audit archived raw evidence without invoking the model or changing its report."""
import argparse
import hashlib
import json
from pathlib import Path
from datetime import datetime, timezone
from document_summary import summarize


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("report", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    raw = args.report.read_bytes()
    original = json.loads(raw.decode("utf-8"))
    summary = summarize(original["events"])
    for name in ("cases", "dna_correct", "always_unknown_correct", "full", "selected"):
        if original["summary"][name] != summary[name]:
            raise ValueError(f"Archived scoreboard disagrees with audit: {name}")
    root = Path(__file__).resolve().parent
    sources = {name: hashlib.sha256((root / name).read_bytes()).hexdigest()
               for name in ("audit_document.py", "document_audit.py", "document_oracle.py",
                            "document_summary.py", "document_dataset.py")}
    audit = {"audited_at": datetime.now(timezone.utc).isoformat(), "run_id": original["run_id"],
             "original_report_sha256": hashlib.sha256(raw).hexdigest(), "auditor_sha256": sources,
             "summary": summary, "model_rerun": False,
             "scope": "Consistency of archived raw evidence; not proof of external truth or tamper-proof origin"}
    with args.output.open("x", encoding="utf-8") as target:
        json.dump(audit, target, indent=2)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
