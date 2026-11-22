# Does the factual guard change what decentralized senders learn?

Use all 16 archived final records from the tribunal passage bank, with both
speaker orders. Apply the existing isolated Qwen factual guard twice per
packet, reversing the letter mapping. Freeze the guard prompt and label
projection. Use mean label logits with the existing label order for ties.

Compare two terminal rewards. Reviewed reward is the archived released score.
The automatic variant replaces the reviewed guard with the model label while
keeping the archived lower-bound rubric score and every other release check.
This isolates one reward component. The lower-bound scores still come from the
archive review.

Fit each reward with and without access to the first sender's choice. Each
fit uses the existing exact expected-return gradients and 256 updates at
0.65 availability. Test greedy policies at 0.45, 0.65 and 0.85 with exact
averaging of nonempty private slates. Cross-score every fit under both
rewards, and compute the probability of selecting a newly released record
and of selecting a reviewed positive record. Report the exact attainable
reward for each information pattern as a check.

This is one exposed tribunal docket with a frozen writer and fixed passage
actions. It tests reward sensitivity. A positive automatic score is separate
from a previously reviewed release and the review uses assistant annotation.
