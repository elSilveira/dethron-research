import test from 'node:test';
import assert from 'node:assert/strict';
import { summarize, shouldAcceptPoll } from '../static/model.mjs';

const event = (kind, data) => ({ kind, data });

test('poll responses from before a start or stop cannot replace newer state', () => {
  assert.equal(shouldAcceptPoll(0, 1, false), false);
  assert.equal(shouldAcceptPoll(1, 1, true), false);
  assert.equal(shouldAcceptPoll(1, 1, false), true);
});

test('empty state never invents measurements or verification', () => {
  const result = summarize({ status: 'idle', events: [], report: null });
  assert.equal(result.baseline, null);
  assert.equal(result.correct, null);
  assert.equal(result.net, null);
});

test('live totals include each task and evaluation cost', () => {
  const result = summarize({ status: 'running', events: [
    event('evolution', { cycle: 1, strategy: 'Plus', version: 1,
      duration_ns: 100, measurement: { evaluation_divisions: 50, promoted: true } }),
    event('task', { input: 97, correct: true, baseline_divisions: 96, evolved_divisions: 5 }),
    event('task', { input: 49, correct: true, baseline_divisions: 8, evolved_divisions: 4 }),
  ] });
  assert.equal(result.baseline, 104);
  assert.equal(result.evolved, 9);
  assert.equal(result.net, 45);
  assert.equal(result.strategy, 'Plus');
  assert.equal(result.tasks.length, 2);
  assert.equal(result.correct, true);
});

test('a failed process cannot turn its last completed event into success', () => {
  const result = summarize({ status: 'failed', report: null, events: [
    event('completed', { correct: true, baseline_divisions: 999 }),
  ] });
  assert.equal(result.completed, false);
  assert.equal(result.baseline, null);
});

test('a wrong task result stays visible', () => {
  const result = summarize({ status: 'running', events: [
    event('task', { correct: false, baseline_divisions: 9, evolved_divisions: 2 }),
    event('task', { correct: true, baseline_divisions: 7, evolved_divisions: 1 }),
  ] });
  assert.equal(result.correct, false);
});
