# Jointly fit a workshop responder and chair with a shared outcome reward

Fit two action heads over frozen Qwen3.5-4B features. The responder sees
its own requirement and the opening note. It chooses whether to disclose
its requirement, endorse the opening package or withhold. The chair reads
the resulting public notes and chooses a package, impasse or unresolved.
Each head adds a learned residual to Qwen's restricted next-token logits.
The exact team return sums over all three message branches. The training
data are 16 synthetic worlds. Both UN workshop families and the actual
archived replies stay out of the optimizer. The constrained test uses a
fixed truthful opener and authored message actions.
[Locked protocol](protocol.md) · [Rewards, prompts and cases](roster.json)

| Policy | Supported correct decisions /8 | Mean greedy return | Truthful replies /8 |
| --- | ---: | ---: | ---: |
| Frozen Qwen | 2 | −0.366 | 6 |
| Joint fit | 2 | +0.065 | 6 |
| Matched bias-only fit | 0 | +0.150 | 8 |
| Joint fit with half-disclosure training mixture | 6 | +0.460 | 8 |
| Fixed truthful disclosure and exact readout | 8 | +0.960 | 8 |

The first joint fit and bias-only fit each use 64 CPU updates. Under
joint fitting the half-disclosure mixture is a third, dependent 64-update
fit from the same initialization. Its optimizer puts half of each
world's probability on a full truthful disclosure and half on the
learned responder distribution. Evaluation uses the trained actors'
unforced greedy choices. The original joint fit earns higher reward
without committing more often. Its chair scores 0/8 when disclosure
is fixed, down from 1/8 for the frozen chair under the same disclosure.
This pointed to a shortage of complete disclosures in the joint training
distribution. [Original comparison](results.json) · [Dependent protocol](disclosure-mixture-protocol.md)

The mixture improves the frozen team's 2/8 to 6/8. It selects full
disclosure in all eight held worlds. The fitted chair resolves 4/4 on
Iraq and 2/4 on Syria. Both Syria agreement orders are wrong, with one
incorrect impasse and one recommendation of A instead of B. The fixed
disclosure ablation reproduces the mixture's greedy results, so these
eight scores give no evidence of an advantage from adaptive messaging
over a fixed disclosure policy. [Mixture traces and policy swaps](disclosure-mixture.json)

On eight archived raw and projected Syria note pairs, the mixture chair
correctly recognizes all four certified impasses. The frozen and original
joint heads defer on all four. In the other four note pairs, the mixture
chair makes four unsupported commitments. The strict ledger calls all four
unresolved because the public notes fail to certify a compatible package.
Two frozen decisions correctly defer on these incomplete or conflicting
transcripts. This transfer is mixed: the intervention improves impasse
recognition and damages deference to incomplete evidence. Keep both
measures visible. The heads are a finite-action policy over fixed model
features. This study provides no new generated diplomatic records or
evidence of improved free-text persuasion or synthesis.

Feature collection encoded 104 prompts on NVIDIA RTX PRO 6000 Blackwell
Server Edition. Qwen's backbone and original output head were frozen.
The optimizer updates only the two finite-action residuals and their
bias-only control. The first CPU attempt reached result serialization
and failed because the provenance builder was missing a Path import.
The corrected run reused the captured features. The verifier reproduces
tokenizer inputs and action IDs, checks feature and logit records, and
replays the original CPU fit exactly.
[Hardware and process receipt](evidence/launch.json) · [Verification](verification.json)

## Verify

From this directory in the project inference environment:

```bash
export PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 HF_HUB_OFFLINE=1
python environment.py | cmp roster.json
python verify.py | cmp verification.json
python disclosure_mixture.py | cmp disclosure-mixture.json
```
