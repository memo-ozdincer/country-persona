# Fit the first send under the frozen question policy

The archived response-aware policy and opening maps are fixed. Change only the
right delegate's decision when no question arrives, including question erasure.
Use the same four public features and 96 full-batch Adam updates at 0.04. Train
on the same development cases, inventory priors and word-budget profiles with
the perfect admission estimate. Weight reward directly by the probability of
reaching each state under the frozen question map. Preserve the response to
every received question byte for byte.

Compare with the archived policy and an exact first-send planner under the
declared public score and perfect admission. The planner conditions on the
same frozen question map. Positive held net change against the archived arm
is required to favor deployment. Report case and budget losses, first-send
changes, the exact no-request comparison and the gap to the held-information
ceiling. The evaluation replays twelve previously examined conditions and
makes no language-model calls.
