"""The V2 expectation table must be tied to the code, not to memory."""
from pathlib import Path
import re
import unittest

WINDOW = Path(__file__).resolve().parents[1]
import sys
sys.path.insert(0, str(WINDOW))
from run_v2_reproduction import (ARTIFACT_SUFFIX, EXPECTED, FAST_EXPECTED, PINNED, REFERENCE_SECONDS,  # noqa: E402
                                 WINDOWS_MAX_PATH, environment, flag_of, path_problems, select)


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


class GuideConsistencyTests(unittest.TestCase):
    """The stranger's guide must quote exactly what the runner expects."""

    def setUp(self):
        self.guide = (WINDOW/'V2_REPRODUCTION.md').read_text(encoding='utf-8')

    def test_fast_suite_counts_in_the_guide_match_the_runner(self):
        ran, skipped = FAST_EXPECTED
        self.assertIn(f'ran={ran} skipped={skipped} PASS', self.guide)
        self.assertIn(f'{ran} e {skipped};', self.guide)

    def test_every_verdict_and_reference_time_is_in_the_guide(self):
        for test, verdict in EXPECTED.items():
            with self.subTest(test=test):
                self.assertIn(f'| `{test}` | `{verdict}` | {REFERENCE_SECONDS[test]} s |', self.guide)


class ProvenanceTests(unittest.TestCase):
    """A summary that does not name its commit cannot be compared with another machine's."""

    def test_the_environment_names_the_commit_and_whether_the_tree_was_clean(self):
        found = environment()
        self.assertIn('commit', found)
        self.assertIn('head', found['commit'])
        if found['commit']['head']:
            self.assertRegex(found['commit']['head'], r'^[0-9a-f]{40} ')
            self.assertIsInstance(found['commit']['modified'], int)


class SelectionTests(unittest.TestCase):
    """A stranger in cmd.exe cannot set PowerShell variables; --only must work instead."""

    def test_no_option_runs_everything(self):
        self.assertEqual(select([]), EXPECTED)

    def test_only_picks_one_milestone(self):
        self.assertEqual(list(select(['--only', 'g3'])), ['test_g3_reference.py'])
        self.assertEqual(list(select(['--only', 'v1_return'])), ['test_v1_return_reference.py'])

    def test_an_unknown_or_missing_name_is_refused(self):
        for argv in (['--only', 'g9'], ['--only'], ['--only', '']):
            with self.subTest(argv=argv), self.assertRaises(SystemExit):
                select(argv)


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
