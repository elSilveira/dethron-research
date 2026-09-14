"""Real token generation and explicit closed-choice neural scoring."""


def prefix(runtime, text):
    tokens = runtime.tokenizer.encode(text, add_special_tokens=True)
    if not 1 <= len(tokens) <= 1024:
        raise ValueError("Prompt outside 1..1024 tokens; truncation is forbidden")
    return tokens


def generate(runtime, request):
    outputs, total = [], 0
    torch = runtime.torch
    for prompt in request["prompts"]:
        tokens = prefix(runtime, prompt)
        ids = torch.tensor([tokens], device=runtime.device)
        generated = runtime.model.generate(
            input_ids=ids, attention_mask=torch.ones_like(ids), do_sample=False,
            max_new_tokens=request["max_new_tokens"], use_cache=True,
            temperature=None, top_p=None, top_k=None,
            pad_token_id=runtime.tokenizer.eos_token_id)
        new = generated[0, len(tokens):].tolist()
        outputs.append({"text": runtime.tokenizer.decode(new, skip_special_tokens=True),
                        "token_ids": new, "input_tokens": len(tokens), "generated_tokens": len(new),
                        "finish_reason": "eos" if new and new[-1] == runtime.tokenizer.eos_token_id else "length"})
        total += len(tokens) + len(new)
    return {"outputs": outputs, "evaluated_tokens": total, "mode": "greedy_completion"}


def rank(runtime, request):
    torch = runtime.torch
    outputs, total = [], 0
    candidates = request["candidates"]
    endings = [runtime.tokenizer.encode(c, add_special_tokens=False) for c in candidates]
    if any(not 1 <= len(c) <= 32 for c in endings):
        raise ValueError("Candidate outside 1..32 tokens")
    tail = max(map(len, endings))
    for prompt in request["prompts"]:
        tokens = prefix(runtime, prompt)
        rows = [tokens + c + [runtime.tokenizer.eos_token_id] * (tail - len(c)) for c in endings]
        masks = [[1] * (len(tokens) + len(c)) + [0] * (tail - len(c)) for c in endings]
        # Retain only logits needed to score candidates, avoiding full-prefix vocabulary tensors.
        logits = runtime.model(input_ids=torch.tensor(rows, device=runtime.device),
                               attention_mask=torch.tensor(masks, device=runtime.device),
                               use_cache=False, logits_to_keep=tail + 1).logits
        scores = []
        for index, ending in enumerate(endings):
            distribution = logits[index, :len(ending)].float().log_softmax(-1)
            selected = distribution.gather(1, torch.tensor(ending, device=runtime.device).unsqueeze(1))
            if not torch.isfinite(selected).all().item():
                raise ValueError("Non-finite candidate likelihood")
            scores.append(selected.mean().item())
            total += len(tokens) + len(ending)
        winner = max(range(len(scores)), key=scores.__getitem__)
        outputs.append({"selected": candidates[winner], "scores": scores,
                        "input_tokens": len(tokens), "candidate_tokens": list(map(len, endings))})
    return {"outputs": outputs, "evaluated_tokens": total,
            "mode": "mean_conditional_log_likelihood", "candidates": candidates}
