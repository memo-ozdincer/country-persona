# Haiti authorization record transfer

On 2 October 2023 the Security Council adopted S/2023/709 as resolution 2699 (2023). Member States were authorized to form and deploy a Multinational Security Support mission in coordination with Haiti's Government. The initial term ran for twelve months from adoption, with review after nine. China and Russia abstained. Mozambique spoke in support of adoption on behalf of the three African Council members. Both the A3 and China supported outside assistance alongside a Haitian political transition. [Official resolution](https://digitallibrary.un.org/record/4022890) · [Official meeting record](https://documents.un.org/api/symbol/access?l=en&s=S%2FPV.9430&t=pdf)

The [accession](accession.json) matches all 15 member votes in the official roll call, UNBench author-test event 2501, and UNSC-Bench adopted row 242. No UNBench author-training row shares the event ID. The project had no previous writer run on this docket. Prior model exposure through pretraining is unknown.

## First-pass writer transfer

Freeze a 70-point final rubric, four documentary cards, five field prompts and three whole-packet controls before inference. The field approach uses separate statements of existing authority, funding and oversight, China's rationale, and Mozambique speaking for the A3. The comparison depends on the two statement cards plus the public vote. The body uses frozen Qwen3.5-4B and the roll call is authored. Both presentation styles receive the same relevant documentary sources for a packet. The sum of separate-field token caps is greater than the primary whole-packet cap. [Frozen case](case.json) · [Acceptance criteria](acceptance.json)

| Matched packet | Separate fields out of 70 | Whole packet out of 70 | Generated tokens, separate and whole | Both release checks |
| --- | ---: | ---: | ---: | --- |
| Safeguards and China | 49 | 35 | 163, 216 | Fail |
| Safeguards and A3 | 49 | 35 | 155, 216 | Fail |
| Both statements | 49 | 35 | 205, 216 | Fail |

The separate fields recover the available factual details in each of the four individual sources. Their comparison preserves opposite vote choices and omits the shared position. It also treats the three African members as speaking for the A3. The whole-packet answers all truncate. The separate fields complete, but the mandate, safeguards and comparison outputs omit their exact source IDs. This gives two releasable records among the 14 reachable field subsets. The rubric reports score, completion, cited IDs and semantic guard independently. Reviews are by the same assistant with exact spans. [First-pass records and accounting](evidence/results.json)

## Separate citation packaging from the statement comparison

Attach the known source ID to the two single-source fields that omitted it. This changes no body words and does not change the semantic review. Eleven of 14 packets then qualify for release. The three packets with both statements still fail because their comparison is wrong. Replace only the comparison with one observed retry using the source-derived shared position and a separate mapping of the two vote choices. It preserves both facts. All 14 now clear release and recover their full licensed criteria. These are targeted follow-ups chosen after first-pass review. [Citation-only and comparison interventions](followup-evidence/results.json)

## Frozen routing on the new case

All routers receive the same archived record for the same set of delivered cards. Both written-vote fits are frozen. The optimized scripted controls can choose reply priority and see the true synthetic roster prior. Neither scripts nor learned policies select routes using the actual generated wording.

| Strong specialist and correct label | First-pass record score | After both targeted repairs | Final net gain after fees |
| --- | ---: | ---: | ---: |
| Original frozen team | 43.22 | 45.80 | 24.319 |
| Specialist-trained team | 43.70 | 46.34 | 24.850 |
| Best fixed script | 43.53 | 46.26 | 24.773 |
| Best adaptive script | 43.84 | 46.62 | 25.133 |
| Pooled with all three required cards | 49.00 | 52.50 | 31.500 |

Under first-pass text, the specialist's release probability is 1.07% despite two individual successful packets. It usually delivers more than one source. Citation attachment raises that probability to 62.26%, and the comparison retry raises it to 100% on this fixed bank. That last result is conditional on the verified replay and the assisted text, with no independent human review. The pooled run has immediate access to all three target cards. [First-pass routes and wrong-label control](evidence/policy-replay.json)

## Match the configured output allowance

Increase only each whole-packet output cap to the sum of the corresponding field caps. The source packet, prompt encoding and checkpoint remain fixed. The generation batches have different sizes, and none of the longer outputs reproduces the original output tokens as an exact prefix.

| Matched packet | Separate fields out of 70 | Whole packet with equal cap out of 70 | Whole record words | Whole record ended |
| --- | ---: | ---: | ---: | --- |
| Safeguards and China | 49 | 49 | 249 | No |
| Safeguards and A3 | 49 | 42 | 232 | No |
| Both statements | 49 | 56 | 299 | Yes |

Both approaches average 49/70 under this comparison. All three enlarged whole records miss the exact citation format and exceed 185 words. The separate records fit the word cap and complete with 155–205 generated tokens, but their original citation and comparison failures persist. The raw score gap disappears under the larger whole-packet allowance. Batch size, input cost and writer calls still differ. [Cap control and raw texts](cap-evidence/results.json)

```bash
export OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
"$MODEL_PY" writer.py replay evidence
"$MODEL_PY" results.py
"$MODEL_PY" policy_replay.py
"$MODEL_PY" comparison_retry.py replay followup-evidence
"$MODEL_PY" followup.py
"$MODEL_PY" cap_control.py replay cap-evidence
"$MODEL_PY" cap_score.py
```
