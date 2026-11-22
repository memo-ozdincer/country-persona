# Generate a native comparison on Resolution 2721

The native editor selects the right source clauses, but the native chair's prose fails to preserve their value. This run freezes the public lead and the received source texts. Qwen3.5-4B writes only an optional comparison. It receives neither the relationship template nor the reward. A same-assistant grade checks the added text against the original sources and the locked task. [Protocol](protocol.md) · [Source rubric and judge instructions](judge.md)

The chair abstains on all five incomplete receipts and on one crossed pair. The other crossed pair ambiguously attributes support for the appointment consultation terms to the African members. In the matched Russian pair, the chair distinguishes consultation from consent but describes a future condition for Russian support as something Russia had already done. In the matched African-members pair, it attributes the envoy's complementary role to the Council. The source attributes that rationale to the African members and records the Council's preservation of the existing mandate. The main grades are six abstentions, two uncertain guards, and one failed guard. A structural rule requiring both source cards leaves all nine results unchanged, since the model already abstains on incomplete inputs. [Native outputs](verified.json) · [Exact spans and grades](marks.json)

| Chair record | Editor reads the receipt | Arrival-only, best for that chair |
| --- | ---: | ---: |
| Verbatim without added comparison | 44.5000 | 44.5000 |
| Verbatim with the native comparison | 17.5000 | 31.0000 |
| Verbatim with the authored comparison | 56.8750 | 50.6875 |

These are exact expected released points at 75% independent delivery and a balanced early-card prior. The best arrival comparator may choose whichever late clause maximizes release for the same writer, using only arrival and the prior. Its native score benefits from one crossed pair where the model abstains. The informed policy reaches both matched pairs and receives zero release on both under the primary marks. If the Russian comparison is accepted as a paraphrase of the prospective condition, the informed editor ties the best arrival policy at 37.1875. If both uncertain comparisons clear, the informed editor again trails, 37.1875 to 50.6875. The result gives no positive native end-to-end advantage under any of these readings. [All 12 simulated conditions and guard sensitivity](scores.json)

The nine calls completed on NVIDIA RTX PRO 6000 Blackwell Server Edition. This experiment isolates the failure of generated comparison text on two positions from one exposed docket. The public lead and notes are authored, delivery is simulated, and there are no language-model weight updates or independent ratings. [Runtime receipt](evidence/launch.json)

## Reproduce

From this directory in the project environment. These checks replay archived tokens and grading.

```sh
set -o pipefail
root=$(git rev-parse --show-toplevel)
export PYTHONPATH="$root/src"
export PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 HF_HUB_OFFLINE=1
py=/mfs1/u/memo/country-persona-research/envs/aurora-qwen35-smoke-v1/bin/python
"$py" generate.py plan | cmp plan.json -
"$py" generate.py verify | cmp verified.json -
"$py" score.py | cmp scores.json -
```
