"""Minimal worker for the G3 channel tests: no Reticulum, same command contract."""
import json
import os
from pathlib import Path
import sys
import time

from g3_process import lines


def main():
    home, name = Path(sys.argv[1]), sys.argv[2]
    events = home/'events.jsonl'

    def emit(event, **values):
        with events.open('a', encoding='utf-8') as stream:
            stream.write(json.dumps({'event': event, 'time': time.time(), **values})+'\n')

    commands = home/'commands.jsonl'
    seen = len(lines(commands))
    emit('ready', pid=os.getpid(), destination=(name*32)[:32], public_key=(name*128)[:128], propagation=(name*32)[:32])
    while True:
        pending = lines(commands)
        for line in pending[seen:]:
            command = json.loads(line)
            if command['action'] == 'crash':
                os._exit(23)
            emit(command['action'], rid=command['rid'], pid=os.getpid(), echo=command.get('value'))
        seen = len(pending)
        time.sleep(.02)


if __name__ == '__main__':
    main()
