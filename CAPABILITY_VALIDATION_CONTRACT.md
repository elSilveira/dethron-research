# Capability validation contract

<!-- dethron-doc-context-20260915 -->
> **Contexto atualizado - 15/09/2026.** Estudo de modelo/avaliação com escopo secundário. Seus resultados não demonstram conectividade mesh, autonomia da internet ou sobrevivência global. Preservar datas e limites dos experimentos abaixo. [Índice atual](README.md) - [Plano de decisão](DETHRON_VALIDATION_PLAN.md) - [Evidências](DETHRON_EVIDENCE_MAP.md).
<!-- /dethron-doc-context-20260915 -->

Date: 2026-09-14. Companion to [the probe plan](PROBE_VALIDATION_PLAN.md).

## Objective

Establish that the system reliably produces correct, useful answers across new inputs and equivalent formulations. Do not require identical prose. Treat plausibility as a candidate for verification, not evidence of truth. These are proposed experiments; no capability or distributed-execution result has been measured by this document.

## Task families and independent checks

| Family | Example and transformation | Acceptance rule |
|---|---|---|
| Arithmetic | `2 + 2`, then fresh operand pairs and changed operations | Parsed numeric answer equals a separately implemented exact oracle; incorrect extra claims fail |
| Composition | `(a + b) + c`, `a + (b + c)` for integers | Both equal the oracle; include negative values, zero and repeated operands |
| Input sensitivity | Change `2 + 2` to `2 + 3` | New result follows new inputs; a constant `4` fails |
| Paraphrase | “The sky is dark” / “Dark is the sky” | Same subject, property, polarity and context; wording may differ |
| Meaning-changing contrast | “The sky is dark” / “The sky is not dark” | Detect changed polarity; reject equivalence |
| Role sensitivity | “Alice follows Bob” / “Bob follows Alice” | Detect reversed roles; bag-of-words overlap cannot pass |
| Quantity and time | “All lights are off” / “Some lights are off”; “was dark” / “is dark” | Do not erase quantifiers or tense; ambiguous context goes to review |
| Missing information | Ask for the color of an unseen object | State insufficient evidence or request needed information rather than invent a fact |

Constrain the first arithmetic suite to integer addition, subtraction and multiplication with a documented output format. A numeric parser must reject missing, ambiguous or contradictory answers rather than extracting any convenient correct number. Broader mathematical equivalence needs its own oracle and domain rules.

For the first language suite, use independently authored, reviewed proposition labels and minimal pairs. A narrow structured proposition comparator is acceptable for this controlled suite, but does not establish general natural-language understanding. Free-form answers outside its coverage require blinded human review with a rubric. Embedding similarity or a model judge can assist triage; neither alone is a correctness oracle. Record reviewer disagreements as INCONCLUSIVE until resolved.

## Distinguishing computation from replay

1. Freeze the candidate implementation, scoring rules and development examples before creating the held-out run.
2. Generate fresh operand combinations from a recorded seed, disjoint from development cases. Keep expected answers in the evaluator, outside candidate requests and worker payloads.
3. Send only task inputs and the declared output schema to the candidate. Capture raw requests, responses, errors and timings before scoring.
4. Independently derive expected arithmetic results in the evaluator. Review semantic labels independently of candidate outputs.
5. Test changed inputs and equivalent formulations together. A system must respond to meaningful changes and remain correct under meaning-preserving changes.
6. Run constant-answer, echo, recorded-answer replay and keyword-only controls through the same scorer. Require every control to fail its designated counterexample set before trusting the scorer.
7. Retain worker execution and handoff evidence for distributed claims. Kill a required worker and ensure a complete successful result is not silently supplied by a local fallback.

Fresh cases and negative controls strengthen evidence against simple replay; finite behavioral tests do not prove the absence of memorization. Correct outputs also do not prove which internal algorithm ran. State these limits in the result rather than demanding unverifiable explanations of internal reasoning.

## Measurements and decisions

Store per-case task ID, family, split, transformation-group ID, input, raw output, expected proposition/result, oracle version, correctness, constraint violations, response status and latency. Store model identity, code hashes, seeds, generation settings and run provenance using P0's evidence contract. Keep evaluator answers separate until the response is captured.

Report the following independently:

- Correctness: correct answers divided by all attempted cases, including timeouts and errors as unsuccessful attempts.
- Coverage: completed, scoreable answers divided by all attempted cases; show abstentions and INCONCLUSIVE judgments separately.
- Paraphrase consistency: groups where every variant is correct and preserves the intended proposition, divided by all tested paraphrase groups.
- Changed-input sensitivity: groups where all required changed answers are correct, divided by all tested contrast groups.
- Reliability and cost: failures, retries, latency and resource use for the same task mix; include all workers.

For the initial controlled smoke gate, require every deterministic arithmetic case and every reviewed semantic minimal pair to pass, and every designated negative control to be caught. This establishes harness readiness only. It is not a population accuracy estimate or a production feasibility result.

Before a larger comparison, freeze per-family quality floors, maximum acceptable quality loss against the baseline, a primary resource objective, sample size and confidence-interval method. Set these from the intended use; do not choose them after seeing results. Compare candidates on paired held-out tasks. Analyze uncertainty at the independent task/group level rather than treating related paraphrases as independent observations. Uncertainty spanning the allowed degradation boundary means INCONCLUSIVE.

An approximate candidate can pass the capability experiment if it meets every declared quality, coverage, reliability and resource gate, even when its prose or logits differ. Report implementation fidelity separately. A failed exact-partition test cannot be relabeled as successful exact execution because the prose sounds reasonable.

## Small implementation slices

Arithmetic scoring and controlled semantic scoring, with their tests, are implemented; the remaining slices below are planned. Semantic labels are currently development fixtures, pending independent review before benchmark use. See [probe usage and scope](probes/README.md). Keep source and test files below 200 lines. Add importable interfaces before each red run so failures exercise behavior.

| Slice | Files | Intended behavioral failure and command |
|---|---|---|
| Arithmetic oracle and scoring | `probes/capability/arithmetic.py`, `probes/tests/test_arithmetic.py` | Constant `4`, wrong results and ambiguous numeric answers accepted; `python -m pytest probes/tests/test_arithmetic.py -q` |
| Controlled semantic scoring | `probes/capability/propositions.py`, `probes/tests/test_propositions.py` | Equivalent word order rejected, or negation/role reversal accepted; `python -m pytest probes/tests/test_propositions.py -q` |
| Held-out generation and controls | `probes/capability/cases.py`, `probes/tests/test_cases.py` | Development overlap or leaked expected answers in candidate payloads; `python -m pytest probes/tests/test_cases.py -q` |
| Execution and accounting | `probes/capability/run.py`, `probes/capability/summary.py`, `probes/tests/test_capability_run.py` | Timeouts disappear from denominators, or consistently wrong groups count as correct; `python -m pytest probes/tests/test_capability_run.py -q` |

After each slice, run `python -m pytest probes/tests -q`. Then connect an identified real candidate through the evidence contract and save an actual baseline run. Passing scorer unit tests is evidence about the scorer, not the model's capabilities.
