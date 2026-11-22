# Reading a combined offer and exclusion

The panel tests whether frozen Qwen3.5-4B can admit two commitments independently. It presents eight short authored messages based on the Mali and outer-space workshops. The candidate package IDs are supplied. The reader receives the named speaker, that speaker's fictional mandate, both package descriptions and the message. It chooses which of two named claims the ledger can admit. Each fixture family contains all four outcomes. A claim must both be made by the named speaker about the current package and follow from the private mandate. No model is asked to invent a diplomatic position.

Each joint decision uses one four-way choice under two label orders. The split reader compares each candidate against rejection under the same two orders, for four model evaluations per bundle. Disagreement across orders or a tie is an abstention. The physical compute differs, and the lock records 48 total evaluations. The authored benchmark checks attribution, conditional wording and substantive inconsistency. It is a targeted low-count diagnostic with no independent human annotations.

The ledger check holds subsequent messages fixed in a recorded Mali path. A missed positive can turn a certified agreement into an unresolved outcome, while a false positive can produce a false agreement certificate. The extra constructed case probes this latter edge. It can expose a false certificate under a frozen suffix. It cannot measure a partner's real response to changed prose.

Cadilhac et al. code elementary discourse units and distinguish offers, counteroffers, acceptance and refusal in negotiation dialogue. Apply the same unit-level distinction here, keeping the speaker and exact condition with each proposition. Record conditional willingness and reported preferences as dialogue events without turning them into current signed commitments. [Negotiation dialogue annotation study](https://aclanthology.org/D13-1035/)

The combined and split readers are evaluation instruments with access to the sender's own private evidence. A deployment that keeps mandates private would perform that check within the sending role and share only the authorized clause or package sign. A recipient can independently check who said what in the public message, with adjudication of the private authority kept separate.

## Model admission and ledger replay

| Method | Exact bundles | True admissions / 8 | False admissions / 8 | Model evaluations |
|---|---:|---:|---:|---:|
| Joint, require same whole answer | 1/8 | 3 | 1 | 16 |
| Joint, retain invariant components | 1/8 | 6 | 2 | 16 shared |
| Separate claim prompts | 2/8 | 7 | 4 | 32 |
| Positive in both joint and separate prompts | — | 3 | 1 | 48 shared |

The joint prompts carry 5,578 input tokens and the split prompts 9,908, summed over both answer orders. The joint reader's false positive is an attribution error. The split reader makes one attribution error and accepts three claims incompatible with the mandate. The latter produces a false E agreement in a constructed Mali boundary test. Both approaches preserve the printed agreement on M1 and M2 and leave conditional M3 unresolved in the fixed-suffix replays. Corroboration leaves one shared false attribution. Keep the valid-claim and false-claim counts separate even when the final ledger state matches. [Raw scoped selections](evidence/predictions.jsonl) · [Paired and component scores](evidence/paired-errors.json) · [Invariant probe](evidence/invariants.json) · [Ledger](evidence/ledger.json)

Applying the archived package-sign gate to the existing joint and split outputs takes no additional model calls. It removes all three mandate errors from the split output and leaves the attribution error. The gated split admits six valid claims and one invalid claim. The projection cannot recover S3's warranted exclusion because the earlier package check for China and F abstained. A speaker-only oracle with the same gate admits at most seven valid claims on these fixtures. [Matched gate control](evidence/gated-comparison.json)

## Separating attribution from mandate verification

The follow-up reads only the speaker and message, with candidate claim names. It then requires a matching order-stable package sign from the previous source checks. The two reversed orders cost 16 new model evaluations and 2,994 input tokens. The archived package-sign cost is outside that number.

| Method | Exact bundles | True admissions / 8 | False admissions / 8 |
|---|---:|---:|---:|
| Original joint outputs with the archived sign gate | 3/8 | 3 | 1 |
| Original split outputs with the same gate | 5/8 | 6 | 1 |
| Separate attribution model prompt, full joint agreement, same gate | 3/8 | 3 | 1 |
| Separate attribution prompt, invariant components, same gate | 4/8 | 5 | 1 |

The factored reader preserves the reported-versus-owned distinction in M2, treats the conditional offer in M3 as unavailable, and prevents the false agreement in M4. It withholds both M1 commitments when its answer changes between label orders, losing a true certificate in the fixed replay. Keeping invariant components recovers M1's positive sign, while its exclusion remains unknown. The China S4 failure persists because the model turns a question relayed by the chair into acceptance. The archived mandate does permit F, so the sign gate cannot detect that error. The gate and a speech-act reader answer distinct questions, and both require validation. [Factored predictions](evidence/factored/metrics.json) · [Component analysis](evidence/factored/components.json) · [Ledger comparison](evidence/factored/ledger.json)

The two model runs and all score projections replay from the archived logits. These are supplied-candidate judgments on eight authored messages in two previously studied families. They test the reading and admission layer before a model can participate through unrestricted prose. No language-policy weights were updated.
