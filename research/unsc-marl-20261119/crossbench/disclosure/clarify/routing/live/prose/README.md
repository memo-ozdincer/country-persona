# Inferring local compatibility menus from prose

Instead of asking the model repeatedly for a single sign, ask it once for all compatible packages under an individual prose mandate. Options are supplied in human-readable language. The prompt contains neither the structured mandate values nor a compatibility label. Five unique role-card prompts cover sanctions impasse, membership overlap, and membership impasse. For each, the structured card remains an evaluator reference.

In dispatch, each delegate's policy observes only its own inferred menu and public evidence. It can use the complement of its predicted acceptable set because the task explicitly requires a complete list. A malformed list yields no claims from that role. The environment compares proposed public signs to the underlying workshop rules before admission. This synthetic safeguard is available because the exact workshop constraints are authored. Compare with the same dispatcher given the structured local menu. Raw model guesses and rejected claims remain documented. The model is never consulted for the other role's condition and no Qwen parameters change.

## Direct menu extraction

Qwen emitted five well-formed lists. Four match the underlying structured constraints. For the United Kingdom's briefings-only membership card, it listed A–F instead of D–F, adding three renewed-review options. On both sanctions parts and the membership agreement case, the policy received exact local observations through the model. On the membership impasse case, it received the model's incorrect UK observations. This is a five-card test. The 27 legal opening pairs per policy reuse the same five model outputs.

| Case | Script with prose readings | Learned policy with prose readings | Script with authored menus | Learned policy with authored menus |
|---|---:|---:|---:|---:|
| Sanctions impasse | 4/6 | 6/6 | 4/6 | 6/6 |
| Membership agreement | 12/12 | 12/12 | 12/12 | 12/12 |
| Membership impasse | 0/9 | 0/9 | 9/9 | 9/9 |

The authors' environment caught 36 rejected signs over the nine impasse opening pairs per arm. None produced a false certificate. Exact sanctions menus restore the structured routing gain with a model controlling the role’s compatibility beliefs. This is still a hybrid protocol. The script and learned policy exchange signs compiled from the model output, without soliciting a new text reply at each turn. [Raw menus](evidence/transcript.jsonl) · [All opening-pair dispatches](evidence/metrics.json) · [Selected final records](evidence/final-records.json) · [Replay](evidence/replay.json)

## Constraint extraction

The second run uses the same five prose cards, with possible attribute values listed independently of their packages. It asks for the explicitly restricted fields and omits unrestricted fields. The environment compiles the output into package choices by exact attribute matching. This changes both the response representation and whether the full package descriptions are shown. It preserves the textual mandates and dated context.

Four outputs again match the gold menus, but the errors move. The model now extracts the UK briefings-only restriction and returns D–F. The France output adds parallel sequencing and chair consultations, though the card explicitly allows either sequence and any product. France accepts only A in this projection instead of A–C. Both routing arms then fail all membership agreement and impasse presentations. The original sanctions routing gain persists. [Raw constraint replies](projection-evidence/transcript.jsonl) · [Projected and compiled menus](projection-evidence/metrics.json) · [Replay](projection-evidence/replay.json)

The direct and constraint methods agree on three menus and disagree on two. A separate adjudication prompt compares only the two candidates on each disputed card. It cannot see the evaluator menu or another role's private text. Prompt order is reversed in a second call, and a choice is admitted only when both calls select the same underlying menu and give a contiguous source excerpt of at least four words. Quote containment checks attribution and exact text; whether the excerpt entails the choice is a separate review.

## Order-swapped menu adjudication

Both ordered France prompts selected A–C and quoted the same sentence of the private card, including the latitude on sequencing and products. The UK prompts cited package descriptions, so neither passed the mandate-quote check. The adapter admitted no menu for that disputed role. Compared with direct lists, the agreement guard preserved the exact sanctions and membership overlap paths while refusing to compile the wrong UK claims. The briefing-only impasse still could not be certified. This is a same-model consistency check with no independent judge. [Order-swapped prompts and replies](reconciliation-evidence/transcript.jsonl) · [Decisions and paths](reconciliation-evidence/metrics.json) · [Replay](reconciliation-evidence/replay.json)

## Field-wise mandate check

The six follow-up prompts use one disputed field at a time, supplying the same card and the allowed values for that field. They omit the package descriptions and historical context. A compiled rule requires an exact quote for every field, including those judged unrestricted. This check identified the UK's briefings-only track with the correct mandate quote, but the UK sequencing answer again quoted option/schema text and failed containment. France produced an exact quote allowing either sequence and used it to justify a parallel-only requirement. Containment passed while semantic entailment failed. The method produced three exact menus and no membership certificates. [Field prompts and replies](field-evidence/transcript.jsonl) · [Outcomes](field-evidence/metrics.json) · [Replay](field-evidence/replay.json)

| Prose method | Exact menus /5 | Sanctions impasse, script /6 | Sanctions impasse, learned /6 | Membership agreement /12, both | Membership impasse /9, both |
|---|---:|---:|---:|---:|---:|
| Direct menu | 4 | 4 | 6 | 12 | 0 |
| Constraint extraction | 4 | 4 | 6 | 0 | 0 |
| Order-swapped reconciliation | 4 | 4 | 6 | 12 | 0 |
| Separate field checks | 3 | 4 | 6 | 0 | 0 |
| Authored structured menus | 5 | 4 | 6 | 12 | 9 |

No model variant certified the membership impasse. The sanctions result is a working hybrid with model-derived local menus and independent verification against authored workshop constraints. The rest of the evaluation shows why quote exactness and even equal menu accuracy give an incomplete picture of protocol performance. These follow-ups are adaptive on the same five cards. The field calibration retains identical-quote examples with different entailment labels for future judge tests. [Semantic scope anchors](field-calibration.json)
