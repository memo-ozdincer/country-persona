# Calibrate frozen Qwen against the v1.7 judge anchors

Use the 21 final-record anchors and four process anchors from the
closed benchmark. Generate from the exact published judge prompts and
schemas using the existing pinned Qwen3.5-4B checkpoint, BF16, greedy
decoding and thinking disabled. Keep the published 4096-token ceiling.
Batch up to four left-padded requests within each judging mode.
Capture every token stream and reuse it in the original calibration
runner without repair or semantic postprocessing.

Report structurally valid verdicts out of all expected packets and
compare valid verdicts with authored targets. Also report raw label
agreement for parseable but invalid verdicts as a separate diagnostic.
No invalid reply counts as usable. A single checkpoint's agreement
with authored anchors is a calibration result and is separate from
independent judge reliability on new outputs.
