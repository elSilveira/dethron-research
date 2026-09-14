"""JSONL service; stdout carries only protocol messages."""
import json
import os
from .protocol import validate


def serve(model, source, target):
    def emit(record):
        target.write(json.dumps(dict(schema=1, pid=os.getpid(), parent_pid=os.getppid(), **record), allow_nan=False) + "\n")
        target.flush()
    emit({"kind": "ready", "data": model.metadata})
    sequence = 0
    while True:
        line = source.readline(65537)
        if not line:
            return
        sequence += 1
        identity = None
        try:
            if len(line) > 65536:
                raise ValueError("Request exceeds line limit")
            request = json.loads(line)
            identity = request.get("id") if isinstance(request, dict) else None
            validate(request)
            data = model.execute(request)
            emit({"kind": "result", "id": identity, "sequence": sequence, "data": data})
        except Exception as error:
            emit({"kind": "error", "id": identity, "sequence": sequence,
                  "error": f"{type(error).__name__}: {error}"[:1000]})
            if len(line) > 65536:
                return
