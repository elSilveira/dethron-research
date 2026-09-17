"""The V2 expectation table must be tied to the code, not to memory."""
from pathlib import Path
import re
import unittest

WINDOW = Path(__file__).resolve().parents[1]
import sys
sys.path.insert(0, str(WINDOW))
from run_v2_reproduction import (ARTIFACT_SUFFIX, EXPECTED, PINNED, REFERENCE_SECONDS,  # noqa: E402
                                 WINDOWS_MAX_PATH, flag_of, path_problems)


class ExpectationTableTests(unittest.TestCase):
    def test_every_expected_test_exists_and_has_one_opt_in_flag(self):
        for test in EXPECTED:
            with self.subTest(test=test):
                self.assertTrue((WINDOW/'tests'/test).exists())
                self.assertRegex(flag_of(test), r'^RUN_GATEWAY_[A-Z0-9_]+$')

    def test_every_expected_verdict_is_produced_somewhere_in_the_sources(self):
        sources = ''.join(p.read_text(encoding='utf-8') for p in WINDOW.glob('*.py') if p.name != 'run_v2_reproduction.py')
        for test, verdict in EXPECTED.items():
            with self.subTest(test=test):
                self.assertIn(repr(verdict).strip("'"), sources)

    def test_every_reference_test_file_asserts_its_verdict(self):
        for test, verdict in EXPECTED.items():
            with self.subTest(test=test):
                self.assertIn(verdict, (WINDOW/'tests'/test).read_text(encoding='utf-8'))

    def test_pins_match_the_requirements_file(self):
        text = (WINDOW/'requirements-gateway.txt').read_text(encoding='utf-8')
        for name, version in PINNED.items():
            self.assertRegex(text, rf'(?m)^{name}=={re.escape(version)}$')

    def test_reference_durations_cover_every_test(self):
        self.assertEqual(set(REFERENCE_SECONDS), set(EXPECTED))


class PathProblemTests(unittest.TestCase):
    """A clone in a long path made all eight real runs inconclusive; the check must catch it first."""

    def test_a_long_repository_path_is_refused_before_any_run(self):
        root = Path('C:/'+'x'*(WINDOWS_MAX_PATH-ARTIFACT_SUFFIX))
        problems = path_problems(root, long_paths=False)
        self.assertTrue(any('too long' in p for p in problems), problems)

    def test_a_short_repository_path_is_accepted(self):
        self.assertEqual(path_problems(Path('C:/dethron'), long_paths=False), [])

    def test_long_paths_enabled_lifts_the_limit_but_not_the_whitespace_rule(self):
        root = Path('C:/'+'x'*(WINDOWS_MAX_PATH-ARTIFACT_SUFFIX))
        self.assertEqual(path_problems(root, long_paths=True), [])
        self.assertTrue(path_problems(Path('C:/my repo'), long_paths=True))


if __name__ == '__main__':
    unittest.main()
