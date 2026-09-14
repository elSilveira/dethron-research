"""Explicit integration tests using local weights, never part of the fast unit suite."""
import os
import gc
import unittest
from neural_worker.model import LocalModel


class RealModelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = LocalModel(os.environ["NEURAL_MODEL_PATH"])

    @classmethod
    def tearDownClass(cls):
        torch = cls.model.torch
        del cls.model
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    def test_identified_resident_model_generates_and_ranks_real_tokens(self):
        self.assertEqual(self.model.metadata.get("load_count"), 1)
        self.assertEqual(self.model.metadata.get("simulated"), False)
        request = {"schema": 1, "id": "generation", "op": "generate",
                   "prompts": ["The capital of France is"], "max_new_tokens": 8}
        first = self.model.execute(request)
        second = self.model.execute(request)
        self.assertEqual(first["outputs"][0]["token_ids"], second["outputs"][0]["token_ids"])
        self.assertGreater(first["outputs"][0]["generated_tokens"], 0)
        ranked = self.model.execute({"schema": 1, "id": "ranking", "op": "rank",
                                    "prompts": ["The capital of France is"],
                                    "candidates": [" Paris", " Tokyo"]})
        self.assertEqual(ranked["outputs"][0]["selected"], " Paris")
        self.assertGreater(ranked["evaluated_tokens"], 0)
