# Resolution 2699 with the public mandate preserved

The public record is the same verified 145-word text in all eight conditions. Qwen3.5-4B wrote each nonempty national section in a single call, with 1,616 input tokens and 856 generated tokens in total. Each section was appended verbatim. All calls finished within the token limit. The composed records run from 145 to 285 words. The empty view uses no model call. [Prospective protocol](protocol.md) · [National source cards and criteria](blind.json) · [Raw generations](final-records.json)

| Received national evidence | Material score | Release score |
| --- | ---: | ---: |
| None | 42 | 42 |
| Ecuador | 42 | 0 |
| China | 49 | 49 |
| Ecuador and China | 49 | 0 |
| Russia | 49 | 49 |
| Ecuador and Russia | 49 | 0 |
| China and Russia | 56 | 0 |
| All three | 56 | 0 |

The whole-record writer released 0/8. Fixing the public section and rewriting only the national accounts yields 3/8. The two isolated abstainer statements and the public record are releasable. The isolated Ecuador statement says Kenya was willing to lead, strengthening its willingness to consider leading. Both generated comparisons of the abstainers ascribe Russia's concern about information before authorization to China. The full view asserts that both delegations had concerns about mission planning and withdrawal details. It passes the two national-account criteria individually and fails the cross-delegation criterion and release gate. Same-assistant scoring marks full narrow qualifications separately from material factual errors. [Original whole-record audit](../facilitator-free-record-bank-evidence/README.md) · [Seven exact-span reviews](review.json) · [Composed records and all edge scores](results.json)

Eight of 12 one-card additions increase material score and four tie. On release, five additions reduce the score, two improve it and five tie. The veto from a bad attribution can outweigh all previously correct evidence. The public and Ecuador singleton reviews alone contradict monotonicity. The independent-interval planner still computes valid nominal bounds. After two further reviews these reach 2.082 points under the uniform inventory prior and 1.910 under correlated inventories. The actual nominal regrets at those prefixes are 0 and 1.423. The budgets here are additional record reviews, with the opening model and transport held fixed.

The score-known requester chooses no requests under either prior. This ties the no-request baseline across the four team replays, which preserve the independent third send. Full-record probability is zero and any-release probability ranges from 24.2% to 37.2%. The metric distinguishes any release from 70-point completeness. With this writer and terminal reward, a communication policy has no measured reason to elicit more evidence. A candidate writer control should validate each delegate's source-bound account before joining them and validate any shared claim against each source. Evaluate the cost and frequency of fallbacks and eligible dissent omitted from a released record before attributing gains to learned communication. This exposed-docket study includes simulated transport, authored scoring criteria and same-assistant review. [Both review paths and matching no-request controls](planning.json)

From the parent directory with the project Python and local model files, replay the pinned transcript and regenerate the review artifacts.

```sh
export OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
python facilitator_fixed_public_bank.py verify facilitator-fixed-public-bank-evidence
python facilitator_fixed_public_bank_score.py blind facilitator-fixed-public-bank-evidence
python facilitator_fixed_public_bank_score.py score facilitator-fixed-public-bank-evidence
python facilitator_fixed_public_bank_score.py plan facilitator-fixed-public-bank-evidence
```
