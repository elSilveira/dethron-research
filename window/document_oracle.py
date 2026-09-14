"""Independent Python reference for the bounded document task, not an LLM judge."""
import json

INSTRUCTION = "Read the handbook evidence. Follow the question's relationships. If evidence is missing or contradicts itself, answer UNKNOWN. Return only JSON with keys answer (short name or UNKNOWN) and citations (section IDs supporting the whole reasoning path; empty for UNKNOWN). Do not add explanations."


def atomic_text(case):
    facts = {}
    for route in case["routes"]:
        query, = route["queries"]
        frontier = {query["entity"]}
        for relation in query["relations"]:
            matches = [s for s in route["sources"] if s["context"] == "document"
                       and s["revision"] == 1 and not s["revoked"]
                       and s["entity"] in frontier and s["relation"] == relation]
            facts.update((s["id"], s) for s in matches)
            frontier = {s["target"] for s in matches}
    return "\n".join(f"[{sid}] {s['entity']} --{s['relation']}--> {s['target']}." for sid, s in sorted(facts.items()))


def inputs(case):
    selected = set()
    for route in case["routes"]:
        query, = route["queries"]
        frontier = {query["entity"]}
        for relation in query["relations"]:
            matches = [s for s in route["sources"] if s["context"] == "document"
                       and s["revision"] == 1 and not s["revoked"]
                       and s["entity"] in frontier and s["relation"] == relation]
            selected.update(s["id"] for s in matches)
            frontier = {s["target"] for s in matches}
    excerpt = "\n\n".join(f"[{sid}] {case['sections'][sid]}" for sid in sorted(selected))
    requests = {mode: {"op": "generate", "prompts": [f"{INSTRUCTION}\n\n{text}\n\nQuestion: {case['question']}\nJSON answer:"],
                       "max_new_tokens": 256} for mode, text in (("full", case["document"]), ("selected", excerpt), ("atomic", atomic_text(case)))}
    return excerpt, requests


def resolve(case):
    conclusions, allowed, proofs = set(), set(), []
    conflict = False
    for route in case["routes"]:
        query, = route["queries"]
        entity, used, complete = query["entity"], set(), True
        for relation in query["relations"]:
            matches = [s for s in route["sources"] if s["context"] == "document"
                       and s["revision"] == 1 and not s["revoked"]
                       and s["entity"] == entity and s["relation"] == relation]
            targets = {s["target"] for s in matches}
            if len(targets) != 1:
                conflict |= len(targets) > 1
                complete = False
                break
            used.update(s["id"] for s in matches)
            entity, = targets
        if complete:
            conclusions.add(entity)
            allowed.update(used)
            proofs.append(used)
    accepted = len(conclusions) == 1 and not conflict
    return {"state": "accepted" if accepted else "abstained",
            "conclusion": next(iter(conclusions)) if accepted else None,
            "source_ids": sorted(allowed) if accepted else [], "proofs": proofs}


def grade(output, reference):
    raw = output["text"]
    final = raw.rsplit("</think>", 1)[-1].strip()
    if final.startswith("```json") and final.endswith("```"):
        final = final[len("```json"):-3].strip()
    try:
        parsed = json.loads(final)
    except (ValueError, TypeError):
        parsed = {}
    if not isinstance(parsed, dict):
        parsed = {}
    answer = parsed.get("answer") if isinstance(parsed.get("answer"), str) else None
    raw_citations = parsed.get("citations")
    citations = sorted({s for s in raw_citations if isinstance(s, str)}) if isinstance(raw_citations, list) else []
    format_ok = answer is not None and isinstance(raw_citations, list) and all(isinstance(s, str) for s in raw_citations)
    complete = any(proof <= set(citations) for proof in reference["proofs"])
    accepted = (format_ok and output["finish_reason"] == "eos" and reference["state"] == "accepted"
                and answer == reference["conclusion"] and complete
                and set(citations) <= set(reference["source_ids"]))
    abstained = (format_ok and output["finish_reason"] == "eos" and reference["state"] == "abstained"
                 and answer == "UNKNOWN" and not citations)
    return dict(answer=answer, citations=citations, format_ok=format_ok,
                accepted=accepted, valid_abstention=abstained)
