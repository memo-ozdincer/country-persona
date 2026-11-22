# Train on recorded reply failures and transfer to Resolution 2719

Train two joint chair-and-responder policies for 96 CPU updates per arm. The measured arm uses the archived binary admission outcomes for Resolutions 2593 and 2699. The ideal arm sees the same authored rewards, inventory priors and physical loss with perfect admission for any valid send. The measured arm's soft request rate falls from 0.530 to 0.049 during training, while the ideal arm's rises from 0.640 to 0.959. The two development dockets share a material-score bank. Resolution 2719 has a distinct score bank and supplies zero optimization inputs. [Locked protocol](protocol.md) · [Training artifacts and traces](fits.json)

## Held-out reply observations

Frozen Qwen3.5-4B produced all 12 combinations of one authorized card and one of four question contexts. The prompts reuse the development runs' 52-word source-rewrite instruction. The rows below mark whole-card admission under the exact-span same-assistant review.

| Question context | Procedure | US | France |
| --- | ---: | ---: | ---: |
| Silence | 1 | 0 | 0 |
| Procedure | 1 | 0 | 0 |
| US | 0 | 1 | 0 |
| France | 0 | 0 | 0 |

Three replies pass. The US answer passes when asked its matched question and loses the explicit interpretation of the original draft when given silence. France answers its matched question with support for assessed financing and a willingness to discuss contribution levels, omitting the predictability part of its objection. Replies to other roles' questions sometimes infer roles or claims from the question itself. Across 12 replies, generation uses 1,898 input and 690 output tokens. A separate authored dependency audit finds two incomplete US replies that can still add six conjunction points when the existing opening already contains Procedure and France. The main policy evaluation uses the locked whole-card gate. [Reviewer instructions](review-instructions.md) · [12 replies, spans and matrix](admission.json) · [Partial-evidence audit](partial.json)

## Transfer results

Both priors use the same frozen opening and the same typed transport and terminal scorer. The plans marked actual receive the held reply matrix; they are hindsight bounds. Every measured entry in the policy replay comes from the same 12 real reply observations and the known authored reward ceiling.

| Policy | Uniform net | Correlated net |
| --- | ---: | ---: |
| Exact no-request with development admissions | 51.045 | 50.229 |
| Measured-admission fit | 51.045 | 50.216 |
| Ideal-admission fit | 53.737 | 53.440 |
| Exact no-request with held admissions | 51.338 | 50.511 |
| Joint exact with held admissions | 54.423 | 53.654 |

The ideal fit beats the declared no-request baseline by 2.691 and 3.211 points, and the hindsight no-request baseline by 2.399 and 2.929. It requests after every opening of positive probability and reaches an 8.2% full-record rate. The measured-admission fit makes no requests under either prior. It ties its declared no-request baseline under uniform inventories and trails by 0.014 with correlated inventories. The noise patterns from the two fitting cases give little credit to question-conditioned evidence admission; the held US question creates that opportunity. [Exact replay and single-cell sensitivity](evaluation.json)

Switching the ideal fit's responder to the measured fit's responder preserves its net result. Removing the question from the discrete responder while the reply writer still sees it reduces gain by just 0.137 and 0.167 points. Keeping the learned discrete response but erasing the question at the reply writer reduces net to 51.132 and 50.327. Erasing both reduces performance to the same-responder no-request result less the paid query fee. The effect is principally a change in what the model writes after seeing the question. Dropping the single successful US-question/US-source cell leaves only 0.067 and 0.086 points of advantage over the declared no-request comparator. [Component and question ablations](ablation.json)

The result demonstrates an interaction benefit in a replay backed by actual model replies. The event is exposed to earlier project work, and each held cell uses one deterministic generation. Physical delivery, source allocation and the final assembly are modeled. The effect depends heavily on a single admitted reply and the responder swap preserves it. This is evidence for the value of the question–reply interface and leaves the generality of joint policy learning unresolved.

## Reproduce from the parent directory

```sh
export PYTHONPATH="$(git rev-parse --show-toplevel)/src"
export OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
evidence=facilitator-measured-channel-evidence
python facilitator_measured_channel_fit.py fit
python facilitator_measured_channel_score.py score "$evidence"
python facilitator_measured_channel_fit.py evaluate
python facilitator_measured_channel_partial.py
python facilitator_measured_channel_ablation.py
```
