# Train both desks on the compact writer's observed release scores

Use the Resolution 2744 compact writer without the previous source
admission gate. This writer releases both valid comparisons and fails
two crossed records. The original typed-reward policy lost to
arrival-only with this writer. Use the actual archived compact scores
for the two local actors' shared terminal reward.

From scratch fit a paired delivery-value sender and a policy-gradient
reply actor. Run the same update count, sample schedule, seed and query
budget with a reply actor that only sees receipt versus silence. Neither
trained actor sees correct comparison labels. Both can learn to
withhold. Their terminal reward includes cost on every attempted send.

Evaluate both learned systems, the previous typed-trained system, the
rubric-only typed sending rule and the best possible arrival-only and
content-aware mappings on the same 96 held settings. Decompose the
largest result into attempted sends, supported comparisons actually
released and guard-rejected double deliveries. Keep a frozen receiver
swap as an attribution check. Then silently substitute the archived
gated compact and topic-guided writer banks during evaluation to test
whether the calibration transfers to another writer. The topic-guided
bank was never used by either learner.

This is outcome-driven training in a simulator over 12 deterministic
receipt scores. New policy optimization does not entail any new
generation or review. The docket, model and marks are exposed. An
improvement relative to arrival-only on held channel and price settings
would establish a routing benefit for this writer, not independent
native deliberation quality or event-family generalization.
