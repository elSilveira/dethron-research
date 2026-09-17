import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


def run(body):
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        (root/'retired').mkdir()
        (root/'retired'/'secret').write_text('old content')
        (root/'live').mkdir()
        (root/'live'/'store').write_text('current content')
        script = 'import sys\nfrom pathlib import Path\nfrom g3_access import install\n'\
                 'root=Path(sys.argv[1]); install(root)\n'+body
        return subprocess.run([sys.executable, '-c', script, str(root)], capture_output=True, text=True)


class AccessTests(unittest.TestCase):
    def test_retired_data_is_blocked_in_fresh_process(self):
        result = run("""
try:
    (root/'retired'/'secret').read_bytes()
except PermissionError:
    print('blocked')
else:
    raise AssertionError('retired source was accessible')
""")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('blocked', result.stdout)

    def test_listing_a_retired_generation_is_blocked(self):
        result = run("""
import os
for call in (lambda: os.listdir(root/'retired'), lambda: list(os.scandir(root/'retired'))):
    try:
        call()
    except PermissionError:
        continue
    raise AssertionError('retired directory was enumerable')
print('blocked')
""")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('blocked', result.stdout)

    def test_live_stores_and_retirement_itself_still_work(self):
        result = run("""
assert (root/'live'/'store').read_text() == 'current content'
(root/'live').rename(root/'retired'/'live')
assert (root/'retired'/'live'/'store').exists()
try:
    (root/'retired'/'live'/'store').read_text()
except PermissionError:
    print('retired after handoff')
else:
    raise AssertionError('data stayed readable after retirement')
""")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('retired after handoff', result.stdout)


if __name__ == '__main__':
    unittest.main()
