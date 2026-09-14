"""One resident, locally loaded Qwen2 checkpoint."""
import os
from pathlib import Path
import time
from .checkpoint import inspect_checkpoint
from .protocol import validate


class LocalModel:
    def __init__(self, path, device="cuda"):
        started = time.perf_counter()
        identity = inspect_checkpoint(path)
        os.environ["HF_HUB_OFFLINE"] = "1"
        os.environ["TRANSFORMERS_OFFLINE"] = "1"
        os.environ["HF_HOME"] = str(Path(__file__).resolve().parent.parent / ".cache" / "huggingface")
        import torch
        import transformers
        from transformers import AutoModelForCausalLM, AutoTokenizer
        if device not in ("cpu", "cuda") or (device == "cuda" and not torch.cuda.is_available()):
            raise ValueError("Requested device is unavailable; no automatic fallback")
        torch.manual_seed(0)
        torch.set_num_threads(4)
        self.torch, self.device = torch, device
        self.tokenizer = AutoTokenizer.from_pretrained(path, local_files_only=True, trust_remote_code=False)
        self.tokenizer.pad_token = self.tokenizer.eos_token
        dtype = torch.bfloat16 if device == "cuda" else torch.float32
        self.model = AutoModelForCausalLM.from_pretrained(
            path, local_files_only=True, trust_remote_code=False, use_safetensors=True,
            torch_dtype=dtype, attn_implementation="sdpa").to(device).eval()
        self.metadata = {"checkpoint": identity, "load_count": 1, "simulated": False,
                         "torch": torch.__version__, "transformers": transformers.__version__,
                         "device": device, "dtype": str(dtype), "load_seconds": time.perf_counter() - started,
                         "parameter_bytes": sum(p.numel() * p.element_size() for p in self.model.parameters())}
        if device == "cuda":
            self.metadata["gpu"] = torch.cuda.get_device_name()

    def execute(self, request):
        from .inference import generate, rank
        validate(request)
        started = time.perf_counter()
        if self.device == "cuda":
            self.torch.cuda.reset_peak_memory_stats()
        with self.torch.inference_mode():
            result = generate(self, request) if request["op"] == "generate" else rank(self, request)
        if self.device == "cuda":
            self.torch.cuda.synchronize()
            result["peak_cuda_allocated_bytes"] = self.torch.cuda.max_memory_allocated()
        result["seconds"] = time.perf_counter() - started
        return result
