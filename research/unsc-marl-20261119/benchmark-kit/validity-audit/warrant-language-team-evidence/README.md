# Give the adaptive chair live model-written opening reports

Take the first two three-delegate workshop domains from a new locked seed. Their grade profiles differ from all preceding fit and test domains under package permutation. Frozen Qwen3.5-4B receives only its own private card in each call. D1 chooses a veto-first disclosure, D2 chooses a highest-grade disclosure, and D3 transcribes only the grade selected by the frozen fitted policy. Authorization confirms the speaker and disclosed grade before creating a public receipt. D3 also has a fixed authorized slot. This makes D1 and D2's choices measured language-model actions. [Locked protocol](protocol.md) · [Runnable prompts and original model](../warrant_language_team.py)

The receiver is frozen from the previous [cross-play experiment](../warrant-requester-evidence/README.md). Compare grade-only planning, the role-factored model with different history lengths, the blended receiver and an oracle given the actual disclosure behavior. Use the full joint distribution of private card types and physical losses with both priors, treating a rejected report as absent before the physical channel. Fit each receiver from sampled ordinary opening histories. Follow-up values and certificates still use the typed workshop protocol. The same evaluation also runs on the scripted opening choices. [Authorization and exact branch replay](../warrant_language_team_score.py) · [Software check](audit.json)

## Free-form disclosures

All 16 free-form outputs from the choosing roles put a package letter in the numeric grade field. Two also leave literal format placeholders. The boundary admits none of those disclosures. All eight D3 transcriptions pass. With only D3's openings, the observed-behavior oracle and all tested receivers tie in every condition. The four-condition mean net is 0.164440, far below the ideal typed control. Receiver learning cannot recover grades absent from the public ledger. [Raw outputs](final-records.json) · [Per-type admissions and scores](results.json)

The first launch stopped before generation when a NumPy integer reached the prompt serializer. The rerun validates the full prompt list before loading the model and uses the same cases. Both the original and corrected language interfaces preserve the resulting outputs in separate directories.

## Package selection with sender-side grade lookup

Require one package letter from the two choosing roles and let the sender compile the attributed numeric grade. Reuse D3's eight exact reports. The model returns a legal package in all 16 calls and all 24 reports now pass authorization. D2 follows the highest-grade rule in 8/8 cases. D1 follows the veto-first rule in 3/8 cases. The replay uses the slots actually selected by the model. In the first domain D1 always selects A, a departure from the instructed convention that still produces an exact authorized grade. [Repair protocol](package-only/protocol.md) · [Model choices and compiled messages](package-only/results.json)

| Domain and inventory prior | Grade-only chair | Role-factored, no history | Blended chair, 16 histories | Actual partner known |
| --- | ---: | ---: | ---: | ---: |
| 0, uniform | 0.823150 | 0.823150 | 0.825200 | 0.825200 |
| 0, correlated | 0.830863 | 0.831037 | 0.830988 | 0.831037 |
| 1, uniform | 0.768030 | 0.765183 | 0.756380 | 0.774409 |
| 1, correlated | 0.836539 | 0.833219 | 0.838646 | 0.840048 |
| Four-condition mean | 0.814646 | 0.813147 | 0.812804 | 0.817674 |

The blended chair improves three conditions and loses 0.01165 in the fourth, leaving its mean 0.00184 below grade-only planning. In the ideal scripted control the blend reaches the known-partner score in every condition. Do not transfer that result to the model's actual disclosure conventions. Exact authorization stabilizes the grade, and strategy variation remains in the selected package. The four conditions come from two domains crossed with two priors. They use exact deployment replay and synthetic historical receipt samples from the observed per-type behavior. The two prompt stages make 24 and 16 actual model calls. Follow-up turns and final certificates remain mechanical.

## Replay

From `benchmark-kit/validity-audit`, use the project Python environment.

```sh
python warrant_language_team.py verify warrant-language-team-evidence
python warrant_language_team_score.py warrant-language-team-evidence
python warrant_language_team_selector.py score warrant-language-team-evidence/package-only
python warrant_language_team_audit.py
```
