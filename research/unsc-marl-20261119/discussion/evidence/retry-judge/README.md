# Myanmar retry judge calibration

The [frozen suite](../../retry_judge.py) gives Qwen3.5-4B the signed and delivered records, a short final workshop statement, and four concrete judgment fields. The fixtures share a source replay with injected channel faults. Two cases preserve the recorded deliveries and reply attempts of the measured immediate and learned traces. Three change one element for calibration, covering an earlier successful delivery, a distinct exclusion added to the resend, and a false assertion that the UN adopted the workshop package. All model inputs and exact answer-code logits are in [the inference records](predictions.jsonl). The ten calls use 12,786 input tokens and zero optimizer updates.

The [reference scorer](anchors.json) checks sender-owned signed ideas, public evidence, turns, and certificate state with and without the resend. The recovered trace has nine turns including the opening, with one resend turn. Removing that turn leaves each role's prior signed-idea inventory intact and removes the public UK acceptance of B. The proof becomes complete at slot seven when India's acceptance arrives. Treating every signed proposition as publicly delivered would falsely certify the undelivered fixture. The authority reference checks the known authored violation in this fixture family.

| Decoder | Correct | Wrong | Uncertain |
| --- | ---: | ---: | ---: |
| Stable fields across both answer orders | 12 | 3 | 5 |
| Retrospective field pooling | 16 | 4 | 0 |
| Typed checks with the model judging authority | 19 | 1 | 0 |

No fixture has all four fields correct under the stable decoder. The recovered trace's proof dependency is wrong in both orders, the added exclusion is missed as a new idea, and the invented authority is accepted. Pooling recovers all five delivery judgments and preserves the authority error. The hybrid comparison applies the existing trace checks to three fields. All five fixtures use one negotiation family and authored reference labels. The probe establishes a concrete failure mode for this judge and format. [Per-field and per-edit audit](paired-audit.json) · [Exact inference replay](replay.json)
