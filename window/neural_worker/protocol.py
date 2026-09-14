"""Bounded JSON protocol shared by the resident worker and Rust client."""


def validate(request):
    if not isinstance(request, dict) or type(request.get("schema")) is not int or request["schema"] != 1:
        raise ValueError("schema must be integer 1")
    if not isinstance(request.get("id"), str) or not 1 <= len(request["id"]) <= 64:
        raise ValueError("id must contain 1..64 characters")
    if request.get("op") not in ("generate", "rank"):
        raise ValueError("Unknown operation")
    prompts = request.get("prompts")
    if not isinstance(prompts, list) or not 1 <= len(prompts) <= 2:
        raise ValueError("Provide 1..2 prompts")
    if any(not isinstance(p, str) or not 1 <= len(p) <= 8192 for p in prompts):
        raise ValueError("Prompts must contain 1..8192 characters")
    if request["op"] == "generate":
        limit = request.get("max_new_tokens")
        if type(limit) is not int or not 1 <= limit <= 256:
            raise ValueError("max_new_tokens must be 1..256")
    else:
        candidates = request.get("candidates")
        if not isinstance(candidates, list) or not 2 <= len(candidates) <= 8:
            raise ValueError("Provide 2..8 candidates")
        if any(not isinstance(c, str) or not 1 <= len(c) <= 64 for c in candidates):
            raise ValueError("Candidates must contain 1..64 characters")
        if len(set(candidates)) != len(candidates):
            raise ValueError("Candidates must be distinct")
    return request
