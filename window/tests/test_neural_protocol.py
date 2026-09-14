import unittest
from neural_worker.protocol import validate


class NeuralProtocolTests(unittest.TestCase):
    def test_limits_reject_bad_or_unbounded_requests(self):
        valid = {"schema": 1, "id": "task-1", "op": "generate", "prompts": ["Hello"],
                 "max_new_tokens": 16}
        self.assertEqual(validate(valid), valid)
        for patch in [{"schema": True}, {"id": ""}, {"prompts": []},
                      {"prompts": ["x" * 8193]}, {"op": "mock"},
                      {"max_new_tokens": 0}, {"max_new_tokens": True},
                      {"max_new_tokens": 257}, {"prompts": ["a"] * 3}]:
            with self.subTest(patch=patch), self.assertRaises(ValueError):
                validate(dict(valid, **patch))

    def test_ranking_requires_distinct_bounded_candidates(self):
        valid = {"schema": 1, "id": "rank-1", "op": "rank", "prompts": ["Answer:"],
                 "candidates": ["MARA", "LENA", "UNKNOWN"]}
        self.assertEqual(validate(valid), valid)
        for candidates in [[], [""], ["x", "x"], [str(i) for i in range(9)], ["x" * 65]]:
            with self.subTest(candidates=candidates), self.assertRaises(ValueError):
                validate(dict(valid, candidates=candidates))
