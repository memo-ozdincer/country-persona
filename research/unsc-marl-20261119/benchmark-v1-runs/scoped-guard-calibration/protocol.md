# Split the factual guard by the source distinction being judged

Use the same 21 authored anchors and 12 reviewed historical finals
as the single-question guard. Keep model, choice labels, both label
orders, decoding and evidence unchanged. Split the guard into three
questions about votes and procedure, force and authority, and
attribution and scope. Check operations of the named instruments,
speaker capacities and ownership of claims. An omitted fact or a
category with no assertion is clear for that question.

Average the two logits for each label within each question. Set
the combined guard to failed if any question fails, or uncertain
if any question is uncertain and none fails. Lock this rule before
capture. Compare error counts with the previous guard. Replay the
historical comparison changing only the guard. Preserve all model
predictions and investigate changes that merely trade false clearance
for false blocking.

This is one frozen Qwen checkpoint and one exposed calibration and
comparison set. No new quote-backed rubric grades or process ratings.
Keep the public benchmark release frozen.
