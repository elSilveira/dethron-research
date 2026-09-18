"""A schedule must be impossible to extend or reinterpret once the window has opened."""
import unittest

from v3_schedule import MAX_WINDOW, digest, plan, schedule, step, validate


def simple(machine='alpha', window=120):
    return schedule(machine, window, [step(0, 'launch', node='A', role='relay', contacts=[]),
                                      step(5, 'announce', node='A'),
                                      step(60, 'status', node='A')])


class ScheduleTests(unittest.TestCase):
    def test_a_well_formed_schedule_round_trips(self):
        one = simple()
        self.assertEqual(validate(one), one)
        self.assertEqual(len(digest(one)), 64)

    def test_steps_must_be_ordered_and_inside_the_window(self):
        for steps in ([step(10, 'status', node='A'), step(5, 'status', node='A')],
                      [step(121, 'status', node='A')],
                      [step(-1, 'status', node='A')]):
            with self.subTest(steps=steps), self.assertRaises(ValueError):
                schedule('alpha', 120, steps)

    def test_an_unknown_action_or_argument_is_refused(self):
        with self.assertRaises(ValueError):
            schedule('alpha', 120, [step(0, 'exec', node='A')])
        with self.assertRaises(ValueError):
            schedule('alpha', 120, [step(0, 'status', node='A', command='rm -rf')])

    def test_every_step_names_a_node(self):
        with self.assertRaises(ValueError):
            schedule('alpha', 120, [{'at': 0, 'action': 'status', 'args': {}}])
        with self.assertRaises(ValueError):
            schedule('alpha', 120, [step(0, 'status', node='not a node')])

    def test_an_unbounded_window_is_refused(self):
        with self.assertRaises(ValueError):
            schedule('alpha', MAX_WINDOW+1, [step(0, 'status', node='A')])
        with self.assertRaises(ValueError):
            schedule('alpha', 0, [step(0, 'status', node='A')])

    def test_the_digest_changes_with_any_edit(self):
        before = digest(simple())
        after = digest(schedule('alpha', 120, [step(0, 'launch', node='A', role='relay', contacts=[]),
                                               step(5, 'announce', node='A'),
                                               step(61, 'status', node='A')]))
        self.assertNotEqual(before, after)


class BenchTests(unittest.TestCase):
    def test_a_bench_declares_one_schedule_and_digest_per_machine(self):
        bench = plan([simple('alpha'), simple('beta')])
        self.assertEqual(sorted(bench['machines']), ['alpha', 'beta'])
        self.assertEqual(bench['digests']['alpha'], digest(simple('alpha')))
        self.assertEqual(bench['window_seconds'], 120)

    def test_one_machine_is_not_a_bench(self):
        with self.assertRaises(ValueError):
            plan([simple('alpha')])

    def test_machines_must_be_distinct_and_share_the_window(self):
        with self.assertRaises(ValueError):
            plan([simple('alpha'), simple('alpha')])
        with self.assertRaises(ValueError):
            plan([simple('alpha', 120), simple('beta', 60)])


if __name__ == '__main__':
    unittest.main()
