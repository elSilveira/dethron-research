# Validation probes

<!-- dethron-doc-context-20260915 -->
> **Contexto atualizado - 15/09/2026.** Estudo de modelo/avaliação com escopo secundário. Seus resultados não demonstram conectividade mesh, autonomia da internet ou sobrevivência global. Preservar datas e limites dos experimentos abaixo. [Índice atual](../README.md) - [Plano de decisão](../DETHRON_VALIDATION_PLAN.md) - [Evidências](../DETHRON_EVIDENCE_MAP.md).
<!-- /dethron-doc-context-20260915 -->

Implemented: independent arithmetic scoring and controlled semantic equivalence.
These are evaluators, not a model or distributed inference runner.

Run from the workspace root:

```powershell
python -m pytest probes/tests -q
```

Example evaluator-side use:

```python
from probes.capability.arithmetic import score_arithmetic

assert score_arithmetic(2, "+", 2, "4").status == "PASS"
assert score_arithmetic(2, "+", 3, "4").status == "FAIL"
```

The candidate receives operands, an operation and instructions to return one
ASCII integer, optionally signed and surrounded by whitespace. Responses are
limited to 1,024 characters including whitespace. Fixtures must use operands
whose expected answer fits this limit. Decimal/scientific notation, expressions,
prose, multiple answers and non-text output fail the controlled response contract.
This narrow arithmetic format is separate from future semantic prose evaluation.

The evaluator computes the expected value with Python integer arithmetic using
its own task inputs. It never evaluates candidate code or extracts a convenient
number from prose. Results preserve expected and observed values and distinguish
incorrect arithmetic from invalid response format. Invalid evaluator inputs raise
an exception so setup mistakes cannot masquerade as model failures.

Tests cover correct results, changed operands against a constant-four response,
negative numbers, zero, large integers, malformed responses and invalid tasks.
The behavioral red run against an always-pass fixture produced 32 failures and
2 passes before implementation. These tests establish scorer behavior only.

## Controlled semantic equivalence

`score_semantics(reference, response)` in `capability/propositions.py` compares
subject, predicate, object, negation, tense and quantifier. Both assertions must
refer to the same context and entities, established by the caller. This scorer
does not determine whether the reference is true in the world.

Supported grammar (case/whitespace and one final period are normalized):

- `the sky/door/light` with `is/was`, or `all/some lights` with `are/were`,
  optional `not`, and `dark/bright/open/closed/on/off`; inverted property-first
  order is also supported, such as `Dark is the sky`.
- Names `Alice/Bob/Carol` with `follows/followed/does not follow/did not follow`;
  corresponding passive forms use `is/was [not] followed by`.

Equivalent supported propositions PASS. Changed fields FAIL equivalence; this
does not necessarily mean contradiction (all and some are not equivalent).
Unknown grammar, pronouns, modal statements, extra clauses and multiple sentences
are INCONCLUSIVE and need review. Identical unsupported text cannot pass merely
by matching itself. No fuzzy similarity threshold or general semantic claim is used.

The semantic behavioral red run against an always-pass fixture had 23 failures
and 11 passes. After implementation, all 34 semantic tests passed. Labels are
development fixtures authored during implementation, not an independently human-
reviewed or held-out benchmark. Unit tests validate the documented grammar only.

Still planned: held-out generation, replay controls,
execution/coverage accounting, provenance validation and an identified real-model
baseline. No model accuracy, generalization or distributed feasibility claim has
been established. See [the capability contract](../CAPABILITY_VALIDATION_CONTRACT.md).
