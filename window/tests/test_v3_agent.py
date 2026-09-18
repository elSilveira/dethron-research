"""An agent must be deaf during its window, and must prove it was."""
import json
from pathlib import Path
import tempfile
import threading
import time
import unittest

from v3_agent import Agent, seal
from v3_schedule import plan, schedule, step


class FakeClock:
    """Monotonic time the test advances by hand, so no test waits on a real second."""

    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        self.now += .01
        return self.now

    def jump(self, seconds):
        self.now += seconds


def bench(window=120, start_wall=None):
    alpha = schedule('alpha', window, [step(0, 'launch', node='A', role='relay', contacts=[]),
                                       step(1, 'announce', node='A'),
                                       step(2, 'status', node='A')])
    beta = schedule('beta', window, [step(0, 'launch', node='D', role='receiver', contacts=[])])
    return plan([alpha, beta], start_wall=start_wall)


class AgentTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.control = self.root/'control'
        self.control.mkdir()
        (self.control/'plan.json').write_text(json.dumps(bench()), encoding='utf-8')
        self.clock = FakeClock()
        self.calls = []

    def execute(self, action, args):
        self.calls.append((action, args['node']))
        return {'ok': True}

    def start(self):
        (self.control/'start.json').write_text(json.dumps({'wall': 1700000000.0}), encoding='utf-8')

    def agent(self, machine='alpha'):
        return Agent(self.root, machine, clock=self.clock)

    @staticmethod
    def rows(agent):
        return [json.loads(line) for line in agent.evidence.read_text(encoding='utf-8').splitlines()]

    def test_a_schedule_that_does_not_match_its_digest_is_refused(self):
        tampered = bench()
        tampered['machines']['alpha']['steps'].append(step(9, 'status', node='A'))
        (self.control/'plan.json').write_text(json.dumps(tampered), encoding='utf-8')
        with self.assertRaises(ValueError):
            self.agent().load()

    def test_a_machine_outside_the_bench_is_refused(self):
        with self.assertRaises(ValueError):
            self.agent('gamma').load()

    def test_every_step_runs_in_order_and_records_its_drift(self):
        self.start()
        agent = self.agent()
        rows = agent.run(self.execute)
        self.assertEqual([call[0] for call in self.calls], ['launch', 'announce', 'status'])
        self.assertEqual([row['position'] for row in rows], [0, 1, 2])
        for row in rows:
            self.assertLess(abs(row['drift']), 1)

    def test_a_failing_step_stops_the_schedule_and_is_recorded(self):
        self.start()

        def explode(action, args):
            if action == 'announce':
                raise RuntimeError('link down')
            return {'ok': True}

        rows = self.agent().run(explode)
        self.assertEqual(len(rows), 2)
        self.assertIn('link down', rows[-1]['error'])

    def test_a_control_channel_touched_during_the_window_fails_the_run(self):
        self.start()

        def meddle(action, args):
            if action == 'announce':
                (self.control/'extra-command.json').write_text('{}', encoding='utf-8')
            return {'ok': True}

        with self.assertRaises(ValueError) as caught:
            self.agent().run(meddle)
        self.assertIn('control channel changed', str(caught.exception))

    def test_the_marker_arriving_after_the_agent_is_not_a_control_change(self):
        # The real order: the agent waits first, and the orchestrator releases the
        # window afterwards. The window begins at the marker, so the seal must too.
        agent = self.agent()
        threading.Timer(.3, self.start).start()
        rows = agent.run(self.execute, timeout=30)
        self.assertEqual(len(rows), 3)

    def test_a_bench_folder_that_was_already_used_is_refused(self):
        # Reusing one mixes two runs' evidence and leaves nodes that cannot relaunch,
        # which showed up as a confusing failure at step 0 on a real bench.
        self.start()
        self.agent().run(self.execute)
        with self.assertRaises(ValueError) as caught:
            self.agent().load()
        self.assertIn('already used', str(caught.exception))

    def test_without_a_start_marker_the_agent_waits_and_then_gives_up(self):
        agent = self.agent()
        with self.assertRaises(TimeoutError):
            agent.run(self.execute, timeout=1)

    def test_how_late_the_window_opened_is_recorded_rather_than_assumed(self):
        self.start()
        agent = self.agent()
        agent.run(self.execute)
        started = [row for row in self.rows(agent) if row['event'] == 'started']
        self.assertEqual(len(started), 1)
        self.assertIsNotNone(started[0]['late_seconds'])
        self.assertIsNotNone(started[0]['local_wall'])

    def test_a_declared_instant_needs_no_marker_and_no_live_channel(self):
        # Two machines cannot share a marker without a channel; they can share an instant.
        instant = time.time()+.4
        (self.control/'plan.json').write_text(json.dumps(bench(start_wall=instant)), encoding='utf-8')
        agent = self.agent()
        rows = agent.run(self.execute, timeout=30)
        self.assertEqual(len(rows), 3)
        started = [row for row in self.rows(agent) if row['event'] == 'started'][0]
        self.assertEqual(started['declared_wall'], instant)
        self.assertGreaterEqual(started['local_wall'], instant)
        self.assertLess(started['late_seconds'], 1)

    def test_the_combined_skew_between_machines_is_readable_from_the_evidence(self):
        # Two machines open their windows at the same instant, so the agents must run
        # concurrently here; running them in sequence would measure this test, not the skew.
        instant = time.time()+1
        (self.control/'plan.json').write_text(json.dumps(bench(start_wall=instant)), encoding='utf-8')
        agents = [Agent(self.root, name) for name in ('alpha', 'beta')]
        threads = [threading.Thread(target=agent.run, args=(self.execute,), kwargs={'timeout': 30})
                   for agent in agents]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=60)
        opened = [[row for row in self.rows(agent) if row['event'] == 'started'][0]['local_wall']
                  for agent in agents]
        self.assertLess(abs(opened[0]-opened[1]), 1, 'machines opened their windows too far apart')


class SealTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)

    def test_a_seal_notices_addition_change_and_removal(self):
        (self.folder/'a.json').write_text('{}', encoding='utf-8')
        before = seal(self.folder)
        (self.folder/'b.json').write_text('{}', encoding='utf-8')
        self.assertNotEqual(before, seal(self.folder))
        (self.folder/'b.json').unlink()
        self.assertEqual(before, seal(self.folder))
        (self.folder/'a.json').write_text('{"x":1}', encoding='utf-8')
        self.assertNotEqual(before, seal(self.folder))


if __name__ == '__main__':
    unittest.main()
