# Carry a frozen learned question through to a published record on Resolution 2719

Use two reachable worlds from the existing evidence-routing fit. The chairman and responder actions come from frozen tables derived from development reward banks. Resolution 2719 was excluded from that fit and previously examined in benchmark development. The archived provenance joins the case to UNBench author-test event 2517. The UN records distinguish adoption of the US amendment by 9–0–6 from unanimous adoption of the final text. [Project provenance](../facilitator-resolution-2719-evidence/provenance.json) · [Official meeting](https://digitallibrary.un.org/record/4031853/files/S_PV.9518-EN.pdf) · [Resolution](https://digitallibrary.un.org/record/4031070)

The two worlds isolate different uses of the question. In the first, receipt of Procedure and US notes leads the learned chair to ask the responder for the France source. The same responder sends a duplicate US source under silence. The declared-channel chair chooses the learned question here. A fixed France comparator sends the generic France note from the same inventory. In the second, receipt of Procedure and France leads the learned chair to ask about the US position. The declared-channel chair remains silent. Both cause the same US source to be sent. The reply texts differ because one archived prompt included the question. [Frozen action table](frozen-actions.json) · [Policy fit](../facilitator-passage-adaptive-fit-evidence/results.json) · [Archived reply matrix](../facilitator-measured-channel-evidence/final-records.json)

All received notes and replies are archived Qwen3.5-4B text. The six distinct downstream writer inputs generate fresh supplementary records. The identical verified decision is appended outside the writer and earns zero comparative points. The archived reply text enters the writer directly. The comparison pairs preserve the opening notes, responder inventory and downstream writer. Identical inputs share one generation. Pooled solo uses three all-source notes from an earlier run, with a higher input token count and different upstream note-generation prompts. [Frozen protocol](protocol.json) · [Assembled records](assembled-records.json)

| World | Path | Material /28 | Release |
| --- | --- | ---: | --- |
| Source changes | Learned and declared | 6 | Pass |
| Source changes | Silence with same responder | 11 | Uncertain |
| Source changes | Fixed France | **13** | **Pass** |
| Wording changes | Learned question | 6 | Uncertain |
| Wording changes | Declared and silence | 6 | Pass |
| Common | Pooled solo | 0 | Pass |

The source-switch question adds France's reason for abstaining. Both France notes also contain willingness to discuss varying UN and EU contribution levels. The learned path's final drops that second fact. The generic fixed-France final retains it and meets the seven-point France criterion. The silence output retains the US rationale and has uncertain release because “Consequently” may assert that the amendment caused the unanimous final vote. With strict release, the question beats that particular silence record, while fixed France remains stronger. The release comparison uses same-assistant judgments of this wording.

In the same-source world, the targeted US reply preserves the original phrase under discussion and the timely-deployment rationale enters the final. Both the targeted and generic replies explicitly mention a contribution limit, and both finals drop it. Neither earns the complete US criterion. The targeted final also blurs whether the original wording already excluded full funding or whether the amendment introduced the exclusion, leaving its release uncertain. Pooled solo preserves the coarse distinction between votes but omits the amendment symbol and none of its position bundles is complete enough to score under these five criteria. [Source-span marks](marks.json) · [Supplement-to-final traces](field-traces.json) · [Sensitivity and token costs](results.json)

Allowing France's affirmative final vote to be inferred from the unanimous tally adds four points to the paths that state the France concern and amendment abstention. The fixed-France advantage over the learned source-switch path remains seven points. Requiring the literal US phrase for the US criterion removes five from the source-switch silence record. This sensitivity changes the raw learned-versus-silence comparison and keeps fixed France ahead. A success in asking for a missing source and a success in retaining a specific reason are distinct endpoints.

These are selected stress worlds from one exposed event, conditional on message delivery. The run tests transfer from a learned discrete routing policy to fresh downstream writing. It supplies no population-average policy result or independent review. Record, at the claim level, which note introduced each qualification and which exact wording survives before assigning terminal credit to the router.

## Verify

Run in the Qwen inference environment from this directory.

```bash
export PYTHONDONTWRITEBYTECODE=1
python score_transfer.py score | cmp results.json
python score_transfer.py records | cmp assembled-records.json
```

The scorer rebuilds the frozen policy paths and exact prompts. It verifies the launch pins, tokenization, unedited model outputs, and the credited and flagged spans.
