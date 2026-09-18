"""Run this machine's part of the bench. One command, one machine, no supervision.

    window/.venv-gateway/Scripts/python.exe window/run_v3_agent.py <bench-folder> <machine>

It loads the schedule, checks it against the declared digest, waits for the shared
instant and then executes its own steps on its own clock. It accepts nothing else,
and it fails loudly if the control folder changes while the window is open.
"""
import json
from pathlib import Path
import sys
import time
import traceback

from v3_agent import Agent
from v3_executor import Executor


def main():
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    root, machine = Path(sys.argv[1]).resolve(), sys.argv[2]
    agent = Agent(root, machine)
    executor = Executor(root, machine)
    schedule = agent.load()
    opens = agent.plan.get('start_wall')
    if opens:
        print(f'window opens in {round(opens-time.time(), 1)}s, {len(schedule["steps"])} steps, '
              f'{schedule["window_seconds"]}s long', flush=True)
    outcome = {'machine': machine}
    try:
        rows = agent.run(lambda action, args: executor(action, args), timeout=1800)
        failed = [row for row in rows if row['error']]
        outcome.update(steps=len(rows), failed=len(failed),
                       verdict='v3_agent_complete' if not failed else 'v3_agent_failed')
    except Exception as exc:
        outcome.update(verdict='v3_agent_error', error=repr(exc), traceback=traceback.format_exc())
    finally:
        executor.close()
    (agent.home/'outcome.json').write_text(json.dumps(outcome, indent=2), encoding='utf-8')
    print(json.dumps(outcome), flush=True)
    return 0 if outcome['verdict'] == 'v3_agent_complete' else 1


if __name__ == '__main__':
    raise SystemExit(main())
