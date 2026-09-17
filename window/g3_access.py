"""A retired generation must be unreachable in the successor process, not merely unused."""
import os
import sys
from pathlib import Path

READS = {'open', 'os.listdir', 'os.scandir', 'os.walk', 'shutil.copyfile', 'shutil.copytree'}


def install(root):
    """Deny reads under root/retired for the rest of this process; retiring still works."""
    retired = Path(root)/'retired'
    prefixes = {os.path.normcase(str(retired.resolve())), os.path.normcase(os.path.abspath(str(retired)))}

    def guard(event, args):
        if event not in READS or not args:
            return
        for value in args[:2] if event.startswith('shutil') else args[:1]:
            if isinstance(value, int) or value is None:
                continue
            try:
                path = os.path.normcase(os.path.abspath(os.fsdecode(value)))
            except (TypeError, ValueError, UnicodeError):
                continue
            if any(path == p or path.startswith(p+os.sep) for p in prefixes):
                raise PermissionError(f'retired generation is unreachable: {value}')

    sys.addaudithook(guard)
    return sorted(prefixes)


def probe(root, relative):
    """Report whether a known retired path is actually unreachable from this process."""
    target = Path(root)/'retired'/relative
    if not target.exists():
        return None
    try:
        target.read_bytes()
    except PermissionError:
        return True
    return False
