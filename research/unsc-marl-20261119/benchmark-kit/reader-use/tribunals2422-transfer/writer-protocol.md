# Test whether delivered claims survive in the final record

Freeze one greedy Qwen3.5-4B writer. It receives all of the curator's
paraphrases for every delivered desk, grouped by speaker, and has 70 words
for its supplement. Use one call for each nonempty receipt. Reuse the
all-evidence receipt for the pooled single writer. The empty receipt has
zero supplementary coverage and no generation. Evaluate all eight masks
and weight them by the frozen policy's receipt distribution. The policies
cannot adapt to writer output.

Review each of the six criteria as fully supported or missing, with an
exact final-record span for each positive mark and a criterion-level reason
for omissions. Give the three joint points only when both required claims
are supported. Check every extra claim against the specific received source
mask. Release requires all factual and attribution guards and at most
70 supplementary words. Report raw coverage, word count, release probability,
and expected coverage under release with zero supplementary points on a
failed record. Add 42 for the supplied Council decision only to separately
reported descriptive totals. Compare changes before and after writer scoring
and report the same communication costs. The scorer receives receipt IDs
and outputs, without policy labels.
