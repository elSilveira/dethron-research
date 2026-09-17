"""Versioned four-mode development inputs; no expected answer in retrieval."""
from collections import Counter
import math
import re

from document_dataset import dataset
from document_oracle import INSTRUCTION, inputs

MODES = ("full", "lexical", "selected", "sentences")
STOPWORDS = set("a an the is are of to in at by its it and or who what where which does do".split())


def terms(text):
    return Counter(t for t in re.findall(r"[a-z0-9]+", text.lower()) if t not in STOPWORDS)


def lexical_ids(sections, question, top_k=4):
    """Cosine TF-IDF, fitted only on available sections; no graph or answer access."""
    if type(top_k) is not int or top_k < 1:
        raise ValueError("top_k must be positive")
    documents = {sid: terms(text) for sid, text in sections.items()}
    frequencies = Counter(t for doc in documents.values() for t in doc)
    idf = {t: math.log((1 + len(documents)) / (1 + n)) + 1 for t, n in frequencies.items()}
    query = {t: n * idf[t] for t, n in terms(question).items() if t in idf}
    query_norm = math.sqrt(sum(v * v for v in query.values()))
    ranked = []
    for sid, doc in documents.items():
        weights = {t: n * idf[t] for t, n in doc.items()}
        norm = math.sqrt(sum(v * v for v in weights.values()))
        score = sum(v * query.get(t, 0) for t, v in weights.items())
        if score and norm and query_norm:
            ranked.append((score / (norm * query_norm), sid))
    return [sid for _, sid in sorted(ranked, key=lambda item: (-item[0], item[1]))[:top_k]]


def sentence_text(case):
    templates = {"team": "{entity} belongs to team {target}.",
                 "lead": "Team {entity} is led by {target}.",
                 "office": "{entity} works at the {target} office.",
                 "backup": "{entity} uses {target} as its backup repository.",
                 "storage": "The {entity} repository stores its material in {target}."}
    selected, _ = inputs(case)
    ids = set(re.findall(r"^\[(S\d+)\]", selected, re.MULTILINE))
    sources = {s["id"]: s for route in case["routes"] for s in route["sources"] if s["id"] in ids}
    return "\n".join(f"[{sid}] " + templates[s["relation"]].format(**s)
                     for sid, s in sorted(sources.items()))


def plan():
    rows = []
    for index, case in enumerate(dataset()["cases"]):
        selected, _ = inputs(case)
        ids = lexical_ids(case["sections"], case["question"])
        texts = {"full": case["document"], "selected": selected,
                 "lexical": "\n\n".join(f"[{sid}] {case['sections'][sid]}" for sid in ids),
                 "sentences": sentence_text(case)}
        offset = index % len(MODES)
        for mode in MODES[offset:] + MODES[:offset]:
            text = texts[mode]
            request = {"schema": 1, "id": f"{case['id']}-{mode}", "op": "generate",
                       "prompts": [f"{INSTRUCTION}\n\n{text}\n\nQuestion: {case['question']}\nJSON answer:"],
                       "max_new_tokens": 256}
            rows.append({"case_id": case["id"], "mode": mode, "evidence": text, "request": request})
    return rows
