# Forecast excerpt costs before replaying a frozen routing policy on Resolution 2466

Resolution 2466 extended MINUJUSTH through 15 October 2019 and requested planning for a successor presence that would include a special political mission. The official roll call records thirteen votes in favour and two abstentions, by the Dominican Republic and Russia. The case joins UNBench author-test event 2273 and UNSC-Bench adopted row 198 by date, document, and all fifteen votes. This event is outside the previous routing fit. A different Haiti mandate from 2023 informed development. [Verified join](provenance.json) · [Official meeting](https://digitallibrary.un.org/record/3800240/files/S_PV.8510-EN.pdf) · [Adopted text](https://digitallibrary.un.org/record/3800047/files/S_RES_2466_%282019%29-EN.pdf)

The prospective packet locks six independent, source-reviewed paraphrases from the France, Russian Federation and Dominican Republic statements. Using a fixed cost for each displayed clause and desk label, enumeration computes what each received source mask can support under a word cap. Two contrasting attributed positions can also earn a four-point comparison criterion. Whole-note planning requires including both statements of a desk together. Excerpt planning can choose either supported statement separately. In both cases communication follows the existing three-source model. The learned controller is the frozen budget-fit model, without further updates. [Packet and source citations](packet.json) · [Locked forecast protocol](protocol.md)

Under modeled uniform inventories at 70 words, the learned team scores 52.990 net and asks once per episode. With the same opening policies, analytical excerpt-aware planning scores 53.095 and asks in 60.3% of episodes. Whole-note planning scores 52.621 and asks in 61.9%. Exact no-request with the same openers scores 52.929. The full source mask can support 16 supplementary points in 70 words under excerpt selection, compared with 11 under whole-note selection. These scores use authored feasibility values and assumed perfect source admission. [Forecast, budget curves and frozen policies](forecast.json)

The program selects two worlds before generation. In the opportunity world the learned and excerpt-planning questions send the missing Dominican Republic source, while the same learned responder under silence duplicates Russia. The fixed missing-source comparator delivers the same Dominican Republic source. In the control world the learned responder would send the Dominican Republic even under silence. Whole-note planning adds no source in either selected world. These are conditional diagnostics. Each path renders identical text for a given source mask, so the model writer cannot benefit from knowing which method sent the note.

## Final-record quality

| Source input | Source words | Available /28 | Free-prose /28 | Free-prose release | Delegation-only /28 | Delegation-only release |
| --- | ---: | ---: | ---: | --- | ---: | --- |
| France and Russia, selected | 49 | 14 | 14 | Fail | 14 | Pass |
| France and Russia, all clauses | 97 | 22 | 19 | Fail | — | — |
| Three desks, selected | 69 | 16 | 6 | Fail | 6 | Pass |
| Three desks, all clauses | 138 | 28 | 8 | Fail | — | — |

All four initial bodies introduce unsupported statements about Council action. Examples include treating Chapter VII as restricted to security and stabilization, claiming the draft was amended to incorporate French language, and saying the Council deferred discussion of the transition. Three bodies also exceed 70 words. The all-clauses three-desk record uses the same prompt for the fully received and pooled-source arms, so it is generated once. Received claims, prose coverage and source-safe release are recorded separately. [Unedited records](assembled-records.json) · [Exact-span review](marks.json) · [Arm-level results](results.json)

The dependent replay keeps both budget-selected inputs and changes the instruction to require one line per delegation with no Council decision account. Both outputs match their requested labels and pass the source review. With two desks the writer retains the full 14 points. With the extra Dominican Republic clause it retains the transition-timing point but drops Russia's explicit human-rights-monitoring scope. The six-point Russia criterion and the linked four-point contrast then lose credit. Under a looser reading that treats the shortened rights reference as sufficient, those ten points would be restored. [Dependent protocol](delegate-only/protocol.json) · [Line-scoped records](delegate-only/assembled-records.json) · [Scored outcomes](delegate-only/results.json)

The literal control combines the same selected curator paraphrases with no writer changes. It retains 14 points in 49 words before the added source and 16 in 69 words after it, so the extra criterion fits alongside the two original positions. The selected opportunity world earns this two-point gain through the learned request, the excerpt planner and the fixed missing-source arm alike. The corresponding dialogue-only format moves from 14 to six points, so the final reward can move against the value of the evidence delivered. In the control world silence delivers the same source as the question. [Constructed literal records](literal-records.json) · [Frozen delivery and generation paths](generation-paths.json)

The previously fitted budget and unbounded controllers tie in five of six additional modeled conditions with the same budget-aware inputs. Their opening decisions match throughout. At 110 words with correlated inventories the budget fit gains 0.225 net points over the unbounded fit. This secondary modeled result comes from the continuation. [Matched-fit control](fit-control.json)

This pilot used pre-reviewed curator text as the actual received evidence and six fresh final-writer calls on one case. It demonstrates prospective applicability of the excerpt budget and a failure to preserve all available evidence in fluent output. Autonomous evidence selection and language-mediated delivery remain unmeasured, and the role-only repair is post hoc. The learned path ties the fixed missing-source arm under literal assembly. No policy parameters or language model weights were updated.

## Reproduce

From this directory in the Qwen inference environment, use the pinned dataset files and the archived policy evidence.

```bash
export PYTHONPATH="$(git rev-parse --show-toplevel)/src" OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
python provenance.py | cmp provenance.json
python plan.py | cmp forecast.json
python fit_control.py | cmp fit-control.json
python literal_assembly.py | cmp literal-records.json
python score_transfer.py score | cmp results.json
python delegate-only/score_delegate.py score | cmp delegate-only/results.json
```

The live replays verify prompt and answer tokens, frozen paths, body evidence and exact cited spans. They read archived generations.
