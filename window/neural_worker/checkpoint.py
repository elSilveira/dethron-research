"""Inspect local model identity without importing or executing model code."""
import hashlib
import json
import math
from pathlib import Path
import struct


def inspect_checkpoint(path):
    root = Path(path).resolve()
    names = ["config.json", "tokenizer.json", "tokenizer_config.json", "model.safetensors"]
    if not all((root / name).is_file() for name in names):
        raise ValueError("Local checkpoint is incomplete")
    config = json.loads((root / "config.json").read_text(encoding="utf-8"))
    if config.get("model_type") != "qwen2" or config.get("quantization_config"):
        raise ValueError("This executor requires the unquantized local Qwen2 checkpoint")
    weights = root / "model.safetensors"
    with weights.open("rb") as stream:
        raw = stream.read(8)
        if len(raw) != 8:
            raise ValueError("Invalid Safetensors header")
        size = struct.unpack("<Q", raw)[0]
        if not 2 <= size <= 16_000_000:
            raise ValueError("Invalid Safetensors header length")
        header = json.loads(stream.read(size))
    tensors = [value for key, value in header.items() if key != "__metadata__"]
    end = 0
    for tensor in sorted(tensors, key=lambda t: t["data_offsets"][0]):
        start, stop = tensor["data_offsets"]
        width = {"BF16": 2, "F16": 2, "F32": 4}.get(tensor["dtype"])
        if width is None or start != end or stop - start != math.prod(tensor["shape"]) * width:
            raise ValueError("Inconsistent tensor layout")
        end = stop
    if not tensors or end + 8 + size != weights.stat().st_size:
        raise ValueError("Tensor payload is incomplete")
    files = {}
    for name in names:
        digest = hashlib.sha256()
        with (root / name).open("rb") as stream:
            for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b""):
                digest.update(chunk)
        files[name] = {"sha256": digest.hexdigest(), "bytes": (root / name).stat().st_size}
    return {"path": str(root), "model_type": config["model_type"],
            "revision_directory": root.name, "files": files, "tensor_count": len(tensors)}
