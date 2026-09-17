# Explicit evidence sufficiency

<!-- dethron-doc-context-20260915 -->
> **Contexto atualizado - 15/09/2026.** Estudo de modelo/avaliação com escopo secundário. Seus resultados não demonstram conectividade mesh, autonomia da internet ou sobrevivência global. Preservar datas e limites dos experimentos abaixo. [Índice atual](../README.md) - [Plano de decisão](../DETHRON_VALIDATION_PLAN.md) - [Evidências](../DETHRON_EVIDENCE_MAP.md).
<!-- /dethron-doc-context-20260915 -->

Protected tasks can opt in by placing `{{evidence_status}}` in their prompt.
After inheriting source facts, the v2 runtime traverses the structured query paths
with the existing verifier. It replaces the placeholder with one of:

- SUFFICIENT: follow current facts and preserve query order. No terminal answer
  is included in this instruction.
- INSUFFICIENT: a required link is missing, inactive, or conflicting; return
  UNKNOWN rather than guessing or inferring a negative fact from absence.

The packet records `evidence_status.sufficient`, issues and deterministic origin.
This is solver-assisted inference: the system supplies answerability information.
It is not evidence that the language model independently learned to judge sources.
Tasks without the placeholder retain their previous prompts and behavior. A task
with the placeholder but without structured DNA is rejected during preparation.

The worker still evaluates the full candidate list or generates text normally.
Raw output is preserved. The existing post-inference assessment remains separate;
an incorrect answer is rejected, never replaced with the verifier's correct
answer. Unsupported answers and abstentions still cannot feed protected children.

Opted-in completed records also expose a separate `decision`:

- Insufficient evidence: `output: UNKNOWN`, `state: abstained`, and
  `origin: dna_sufficiency_gate`. A wrong raw model guess remains in `output` at
  the record level and remains rejected in `assessment`.
- Sufficient evidence and correct model answer: `origin: verified_model_answer`.
- Sufficient evidence but wrong/truncated model answer: no delivered answer.

Consumers of this mode must read `decision.output` for the delivered answer and
retain `record.output` for model evaluation. Existing generic raw-output views
are not changed into delivered-answer views automatically. The network journal
stores the decision as part of its record. A system abstention is not a repaired
substantive answer and does not prove improved neural accuracy. Failed calls are
still failures; the gate does not fabricate a model completion.

The contract is tied to caller-supplied structured queries and sources. It does
not parse arbitrary prose, prove external truth, or infer arbitrary logical
negation. A `not_assigned_to` query requires that exact explicit relation; absence
of `assigned_to` is not evidence for it. General positive/negative contradiction
reasoning across distinct predicate names is not implemented.

Connected execution: preserve the task plan with its placeholder, restore it
from encrypted linked units, then let the worker runtime compute sufficiency
from recovered facts. No expected test answer is included in the preserved plan.
The fixed schema, recovery limits, root/key ownership and replica limitations in
[CONNECTED_RECOVERY.md](CONNECTED_RECOVERY.md) continue to apply.

Validation uses the previous 16 development cases plus 16 additional variations
with new entities, changed wording, and C/D supported targets. This is one bounded
development suite, not an independently authored natural-language benchmark.
Report raw correctness, supported coverage, unsupported abstention and false
acceptance separately; always-UNKNOWN is an explicit 24/32 control.
