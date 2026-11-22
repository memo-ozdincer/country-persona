# What the team learns when the writer controls the terminal reward

With the native writer as its reward, the trained editor learns to avoid the receipt pairs that support the intended comparisons. A mandatory-send policy substitutes a mismatched clause. When silence is allowed, the team also withholds a clause that would complete the African members' comparison. The higher native release score therefore comes at the cost of grounded evidence coverage.

Train the same two-source residual estimator with matched draws of private availability, delivery and exploratory actions. The learner receives one final score and the IDs that arrived. It gets a deterministic source-bound score, a deterministic score from the previously graded native writer, or an unlabeled mixture choosing those two writers with equal probability. The estimator and decoder are otherwise identical. [Protocol](protocol.md) · [Plan and archived inputs](plan.json)

| Training score at 256 exchanges | Send requirement | Source-bound release | Native release | Supported pair reaches chair | Late desk sends |
| --- | --- | ---: | ---: | ---: | ---: |
| Source-bound | Mandatory or optional | 53.96227 | 19.80545 | 48.80% | 100.00% |
| Native | Mandatory | 45.80619 | 31.51636 | 11.72% | 100.00% |
| Native | Optional | 41.76341 | 41.76341 | 0.00% | 67.05% |
| Mixed | Mandatory | 48.17544 | 30.92167 | 22.49% | 100.00% |
| Mixed | Optional | 43.88677 | 38.14950 | 8.20% | 74.25% |

Each mean covers 11 channel conditions outside the collection condition and 256 simulated training histories. The pair coverage measure checks the delivered source IDs independently of the writer score. It does not count inferred comparisons or word overlap. The source-bound fit produces the informed matching policy in the shown budget. [Paired writer crossover](results.json)

At 75% delivery with equal availability, all 256 optional native fits send the UNAMA clause after seeing Russia's note and remain silent after seeing the African members' note. The same policies gain **25.3125** points on the native writer and lose **14.0625** on the source-bound scorer relative to the matching policy. When forced to send, the native fit still switches away from the matched Russian clause in every history.

Under the strict native grades, optional native-trained policies gain 21.96 mean points over the authored-trained matching policy on that writer. If the uncertain Russian matched comparison clears, the average gain falls to 4.88 and reverses in some channel conditions. Delivery of the registered supporting pairs remains zero under the optional native-trained policy because neither reevaluation changes its choices. Those distinctions keep uncertainty about the native reward separate from evidence coverage.

This is one exposed docket with archived same-assistant grades and modeled channel behavior. It measures how a joint outcome learner adapts to downstream writer failures. It neither estimates unseen event transfer nor changes the model backbone.

## Reproduce

From this directory:

```sh
set -o pipefail
export PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1
py=/mfs1/u/memo/country-persona-research/envs/aurora-qwen35-smoke-v1/bin/python
"$py" crossover.py plan | cmp plan.json -
"$py" crossover.py run | cmp results.json -
```
