import copy
import unittest
import json
from document_dataset import dataset

INSTRUCTION = "Read the handbook evidence. Follow the question's relationships. If evidence is missing or contradicts itself, answer UNKNOWN. Return only JSON with keys answer (short name or UNKNOWN) and citations (section IDs supporting the whole reasoning path; empty for UNKNOWN). Do not add explanations."
from document_summary import summarize


class DocumentSummaryTests(unittest.TestCase):
    def evidence(self):
        document = dataset()
        cases = document["cases"]
        events = [{"kind": "document", "data": document},
                  {"kind": "worker", "data": {"handshake": {"data": {"simulated": False}}}}]
        for case in cases:
            modes = [{"mode": mode, "answer_correct": case["expected"] == "UNKNOWN", "seconds": 1,
                      "assessment": {"answer": "UNKNOWN", "citations": [], "format_ok": True,
                                     "accepted": False, "valid_abstention": case["expected"] == "UNKNOWN"},
                      "response": {"data": {"evaluated_tokens": 10,
                          "outputs": [{"text": json.dumps({"answer": "UNKNOWN", "citations": []}),
                                       "input_tokens": 9, "generated_tokens": 1, "token_ids": [1],
                                       "finish_reason": "eos"}]}}} for mode in ("full", "selected")]
            supported = case["expected"] != "UNKNOWN"
            ids = sorted({s["id"] for r in case["routes"] for s in r["sources"]}) if supported else []
            dna = {"state": "accepted" if supported else "abstained",
                   "conclusion": case["expected"] if supported else None, "source_ids": ids}
            selected_ids = sorted({s["id"] for r in case["routes"] for s in r["sources"]})
            excerpt = "\n\n".join(f"[{sid}] {case['sections'][sid]}" for sid in selected_ids)
            for m in modes:
                text = case["document"] if m["mode"] == "full" else excerpt
                m["request"] = {"op": "generate", "prompts": [f"{INSTRUCTION}\n\n{text}\n\nQuestion: {case['question']}\nJSON answer:"], "max_new_tokens": 256}
            events.append({"kind": "case", "data": dict(case, selected_text=excerpt, dna=dna, dna_correct=True, modes=modes)})
        return events + [{"kind": "complete"}]

    def test_constant_abstention_does_not_inflate_supported_coverage(self):
        summary = summarize(self.evidence())
        self.assertEqual(summary["always_unknown_correct"], 3)
        self.assertEqual(summary["full"]["answer_correct"], 3)
        self.assertEqual(summary["full"]["supported_correct"], 0)
        self.assertEqual(summary["selected"]["accepted"], 0)

    def test_partial_runs_and_changed_scores_cannot_become_completed_evidence(self):
        events = self.evidence()
        with self.assertRaises(ValueError):
            summarize(events[:-1])
        changed = copy.deepcopy(events)
        changed[2]["data"]["modes"][0]["answer_correct"] = True
        with self.assertRaises(ValueError):
            summarize(changed)

    def test_tampered_acceptance_evidence_modes_and_costs_fail_closed(self):
        mutations = [
            lambda r: r["modes"][0]["assessment"].update(accepted=True),
            lambda r: r["dna"].update(conclusion="invented"),
            lambda r: r["modes"].append(copy.deepcopy(r["modes"][0])),
            lambda r: r["modes"][0]["response"]["data"].update(evaluated_tokens=1),
            lambda r: r["modes"][0].update(seconds=float("nan")),
            lambda r: r["modes"][0]["response"]["data"]["outputs"][0].update(text='{"answer":"Mira","citations":["S1","S2"]}'),
            lambda r: r["routes"][0]["sources"][0].update(target="invented"),
            lambda r: r["modes"][0]["request"].update(prompts=["Leaked expected answer: Mira"]),
            lambda r: r.update(selected_text="Changed selected evidence"),
        ]
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                events = self.evidence()
                mutation(events[2]["data"])
                with self.assertRaises(ValueError):
                    summarize(events)
