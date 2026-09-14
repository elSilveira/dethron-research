import json
from pathlib import Path
import struct
import tempfile
import unittest
from neural_worker.checkpoint import inspect_checkpoint


class CheckpointTests(unittest.TestCase):
    def test_checks_files_architecture_offsets_and_records_actual_hashes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with self.assertRaises(ValueError):
                inspect_checkpoint(root)
            (root / "config.json").write_text(json.dumps({"model_type": "qwen2"}))
            (root / "tokenizer.json").write_text("{}")
            (root / "tokenizer_config.json").write_text("{}")
            header = json.dumps({"weight": {"dtype": "BF16", "shape": [2], "data_offsets": [0, 4]}}).encode()
            weights = root / "model.safetensors"
            weights.write_bytes(struct.pack("<Q", len(header)) + header + b"\x00" * 4)
            metadata = inspect_checkpoint(root)
            self.assertEqual(metadata["model_type"], "qwen2")
            self.assertEqual(metadata["tensor_count"], 1)
            self.assertEqual(len(metadata["files"]["model.safetensors"]["sha256"]), 64)
            weights.write_bytes(weights.read_bytes()[:-1])
            with self.assertRaises(ValueError):
                inspect_checkpoint(root)

    def test_missing_checkpoint_cannot_be_replaced_by_another_model(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValueError):
                inspect_checkpoint(Path(directory) / "missing")
