# Score one rubric item at a time with constrained labels

Reuse the three disputed records, three controls and six archived
source-support verdicts from the separated judge. Replace only the
coverage stage. The same frozen Qwen3.5-4B reads candidate text and
one criterion per request. No historical source excerpts, scores,
weights, prior verdicts or control labels enter the prompts.

Use two mappings between answer letters and statuses. One maps A to
met and B to unmet. The other swaps those two meanings. C always
means uncertain. Score the next-token logits for the three legal
letters and select the largest. A criterion is uncertain when the
two mapped decisions disagree or either choice is uncertain. Keep a
single-mapping diagnostic. An uncertain record keeps its former
routing grade. The already verified whole-record guard still applies.

Run a whole-candidate atomic comparator. The scoped arm limits
supplemental criteria on the pre-existing modular record to candidate
paragraphs with the owning source tag. When no such paragraph appears,
the scoped arm assigns unmet without a model call. The Myanmar record
has no source tags and shares its coverage reading across arms. The
plan scores 53 distinct item-and-view prompts under two mappings,
or 106 scorer invocations from one checkpoint load. Score content and
format separately. The emitted ID is selected from legal logits and
the runner adds a terminal token for its output trace.

Use the six records' original weights, protected public bases and
guards. Evaluate criterion identity as well as total score. Replay
the 23 archived trigger conditions using each admitted pair grade
and the same routing code. Report per-arm candidate count, exact
grades, uncertainty, routing utility and any difference from the old
source-tag replay. These exposed cases support a component diagnosis.
