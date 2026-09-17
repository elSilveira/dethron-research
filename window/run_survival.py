"""Run the same measured survival probe as the Window button."""
import argparse
import json
import time
from survival_dashboard import SurvivalManager


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs", type=int, default=3)
    args = parser.parse_args()
    manager = SurvivalManager()
    try:
        print(json.dumps(manager.start(args.runs)), flush=True)
        previous = None
        while manager.thread.is_alive():
            state = manager.snapshot()
            latest = state["events"][-1] if state["events"] else None
            phase = (latest["trial"], latest["kind"]) if latest else (0, "build")
            if phase != previous:
                print(f"trial={phase[0]} stage={phase[1]}", flush=True)
                previous = phase
            time.sleep(0.2)
        state = manager.snapshot()
        print(json.dumps({"status": state["status"], "run_id": state["run_id"],
                          "summary": (state.get("report") or {}).get("summary"), "error": state.get("error")}), flush=True)
        return 0 if state["status"] == "completed" else 1
    finally:
        manager.close()


if __name__ == "__main__":
    raise SystemExit(main())
