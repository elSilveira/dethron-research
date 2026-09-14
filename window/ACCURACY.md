# Accuracy harness and evidence DNA

The network now separates successful execution from an acceptable answer.
Each completed call keeps its raw `output` and adds an `assessment`: accepted,
rejected, abstained, truncated, or unverified. The verifier never replaces an
incorrect neural answer with its own correct answer.

## Measured result

Evidence: `results/network-20260914T133626Z-a537cd65/`, 14 September 2026.
The saved source hashes were checked against the implementation. One resident
local DeepSeek model ran on CUDA. This evaluates accuracy, not concurrency.

| Configuration | Raw correct / 40 | Accepted substantive answers | Wrong accepted | Answerable-case coverage |
| --- | ---: | ---: | ---: | ---: |
| Raw instructions and full evidence | 5 | 5 | 0 | 25% |
| Examples and full evidence | 23 | 3 | 0 | 15% |
| Examples and recognized evidence | 35 | 20 | 0 | 100% |

The evaluation includes 20 supported questions, balanced across A/B/C/D, and
four each with missing, contradictory, stale, revoked, or foreign-context facts.
Always answering UNKNOWN scores 20/40. The examples-only configuration mostly
abstained; its higher raw score does not mean it answered more useful questions.

Recognition follows the declared relation path and selects relevant current
sources. It preserves contradictory sources rather than choosing a convenient
answer. With recognition, all 20 supported questions were answered correctly;
15 of the 20 unsupported questions received UNKNOWN. Five unsupported guesses
remained wrong and were rejected by the independent acceptance check. Among the
20 accepted substantive answers, precision was 100% in this small test.

Eight additional expansion cases each stored 130 sources, about 20 KB of
structured data. Recognition selected two relevant facts per case, fitting the
existing packet and prompt limits. All eight model answers were correct and
accepted. A two-task wave also passed: the child inherited the parent's original
source facts and produced another accepted answer.

The narrow expansion gate passed: zero wrong accepted answers, at least 75%
answerable-case coverage on both evaluation and expansion sets, and two accepted
connected-wave answers. This is a development gate, not statistical evidence of
production reliability. No threshold or prompt was changed after observing these
results. The calibration and evaluation entities are disjoint, but share the same
synthetic templates. This is not an independent natural-language benchmark.

The deterministic relation-lookup control solved every case. Consequently this
experiment establishes improved neural evidence use and filtering, not an
advantage over structured retrieval. The previous 25% network result used different
questions and two CPU workers; it is not a direct before/after accuracy comparison.

## Reproduce

```powershell
python run_network.py --experiment accuracy --workers 1 --device cuda
```

The report preserves all seven trials (three calibration, three evaluation, one
expansion), source corpora, requests, model replies, assessments, citations, raw
accuracy, accepted precision, coverage, constant baseline, deterministic control,
tokens, preparation time, and execution time. It contains 154 measured model
calls plus one worker preflight. `status.json` reports `expansion_ready` separately
from execution completion.

## Packet contract

Custom tasks can add this `dna` field alongside their existing context, revision,
prompt, and candidate settings:

```json
{
  "sources": [
    {"id": "source-1", "context": "project-7", "revision": 1,
     "entity": "parcel", "relation": "stored_at", "target": "locker", "revoked": false},
    {"id": "source-2", "context": "project-7", "revision": 1,
     "entity": "locker", "relation": "assigned_to", "target": "B", "revoked": false}
  ],
  "queries": [{"entity": "parcel", "relations": ["stored_at", "assigned_to"]}]
}
```

A `{{evidence}}` placeholder in the prompt is replaced with source evidence;
without it the evidence is prepended. The verifier follows the declared path
through current, non-revoked sources. Multiple queries require the terminal
answers in query order, separated by comma-space. This is an exact structured
relation verifier, not a general semantic verifier for arbitrary prose.

Packet schema 2 carries source identities, context, revision, revocation flags,
queries, and parent assessments. A protected child must receive accepted parent
answers. It can declare an empty source list to inherit parent sources. Reusing
a source ID with different content across waves is an error. Revisions require a
new consistent task graph; there is no live revocation service during inference.

Source IDs identify caller-supplied records. They are not signatures or proof of
external truth. Acceptance means entailment from those supplied records. A false
but internally consistent input fact can still produce an accepted answer.

Unsupported guesses, abstentions, and truncated generations cannot feed a later
wave. Tasks without DNA remain explicitly unverified and can feed other legacy
unprotected tasks, provided generation ended normally. In particular, the older
generation demo may now block synthesis when a parent reaches its token limit;
this is intentional and its partial report remains available.

Recognition is exposed through `Dna::recognize` and used by the accuracy harness.
Custom task configurations are not silently pruned: callers must select their
sources explicitly. Limits remain 512 source records, four queries, four relation
steps, 8 KB packets, and the worker's 1,024-token prompt maximum. Large stored
corpora are retrieved from; they are not all placed in the model's attention window.

## Next expansion decision

Proceed with a bounded context-shard experiment, keeping the plain worker pool as
the baseline. Use facts spread across shards, cross-shard questions, irrelevant
documents, contradictions, and source updates. Measure raw accuracy, accepted
precision, coverage, source retrieval recall, and total cost together. Include
structured retrieval and a competent text-retrieval baseline.

Before broad deployment, use independently authored questions and varied wording,
test evidence extraction from real documents, and test revocation while work is
in flight. The remaining five unsupported guesses show why the acceptance check
must remain separate from the model. Multi-machine scaling can follow without
treating more workers as an accuracy improvement.

Verification passed: 19 Python tests, 56 Rust tests, five JavaScript tests, Clippy,
and formatting. New behavior was tested failing first; source and test files are
within 200 lines. Cross-machine SSH execution was not exercised in this milestone.
