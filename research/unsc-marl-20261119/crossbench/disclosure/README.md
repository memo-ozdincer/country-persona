# Iraq language delegates and verifiable disclosures

This bounded baseline uses the previously audited Iraq UNAMI workshop pair. The two cases share the real dossier, package descriptions and France's private workshop requirement. Only the United Kingdom's simulated condition differs. The feasible case shares option A, and the impasse case has disjoint nonempty menus. These conditions are fabricated for the workshop. The prompt makes no claim about either delegation's real policy or future vote. [Benchmark linkage and case design](../README.md)

## Protocol

Qwen3.5-4B acts as both delegates in separate calls. Each round permits at most one signed option claim per role. The model must return JSON with separate accepts and excludes lists. An empty message is a pass. The environment rejects malformed or untruthful output, keeps the raw response, and forwards only admitted first-round disclosures. The peer comparison receives the same own opening and the actual admitted peer opening. The solo comparison has no peer opening. Within a round the two disclosures are simultaneous. Shared France openings and solo continuations are evaluated once because their inputs are identical across variants.

The readout sees only public admitted messages. It verifies agreement on an explicitly supported common option or verifies impasse once every package has an exclusion. An unresolved outcome can be sound when those proof conditions are absent. The evaluation reference independently checks the complete private menus. Factual prose, political fidelity and formal votes are outside this actor-interface score.

The experiment is zero-shot with a frozen policy and two equal-budget arms. Each completed arm has four 64-token allocations. Greedy native decoding uses the pinned Qwen3.5-4B revision with thinking disabled on CPU. The fixed comparison includes support-first, exclusion-first, and a public-A probe with truthful reports based on each role's own menu.

## Information-budget audit

Across all 225 ordered pairs of nonempty four-option menus, 175 have overlap and 50 are disjoint. The hindsight capacity calculation asks whether a proof can even be transmitted with a fixed number of signed claims per role. It knows both private menus and is an upper bound, rather than a decentralized behavioral baseline.

| Claims per role | Agreements certifiable /175 | Impasses certifiable /50 |
|---:|---:|---:|
| 1 | 175 | 0 |
| 2 | 175 | 42 |
| 3 | 175 | 50 |

In the eight inaccessible cases at budget two, one side accepts three and the other accepts only the remaining option. The singleton side must exclude three packages to prove impasse. Outcome-only reward cannot turn those cases into certified impasses without changing the messages or budget.

The public-A probe solves the two specific Iraq workshop cases. Across all 225 ordered menu pairs it solves 64 agreements and seven impasses. Support-first resolves 153 agreements and no impasses. Exclusion-first resolves 14 impasses and no agreements. A benchmark containing just the Iraq pair would overstate the public-A probe's generality. [Capacity and scripted-policy replay](capacity.json)

## Measured language results

| Response format | Unique raw calls | Admitted nonempty claims | Peer turns that received a claim | Solo verified outcomes | Peer verified outcomes |
|---|---:|---:|---:|---:|---:|
| Two lists with a one-claim limit | 10 | 0 | 0/4 | 0/2 | 0/2 |
| Single scalar stance and option | 10 | 10 | 4/4 | 1/2 | 1/2 |

In the list run, nine outputs were valid JSON but exceeded the one-claim budget. The tenth was a valid pass. Five of the over-budget replies also contained an untruthful option claim if audited before budget rejection. Those outputs were preserved and excluded from the ledger. The scalar rerun changed the output instruction and admission parser while preserving the underlying case and initial role views, checkpoint, decode caps, public routing format, and greedy decoding. Rerun turn histories correctly reflect the newly admitted openings. Its initial preflight hit an import-order error before model startup. Importing the scalar wrapper first fixed that setup error.

All ten scalar replies were valid, truthful, and under the turn cap. France accepted A in both cases. The UK accepted A in the agreement case and C in the impasse. The opening already established the overlap. Every second-turn scalar output repeated its own opening, even when the other opening contradicted the possibility of the same selected package. Both scalar arms therefore left the impasse unresolved with zero exclusions. The format repair enabled interaction and exposed a behavior problem that the earlier list run could not test. [Interface comparison](interface-comparison.json) · [Scalar token and routing replay](scalar/evidence/replay.json) · [List replay and rejected text](evidence/replay.json)

Only the Iraq workshop pair was tested. These results measure explicit simulated claims and proof outcomes, with no historical judgement or natural-language endings in the rubric. The 4B checkpoint stayed frozen. For 3-option training and 4-option structured policy evaluation under this same disclosure budget, see [the controlled MARL comparison](LEARNING.md).
