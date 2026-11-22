# Preparation record

The first CPU process was stopped before the first update after a
review caught a missing hint axis in the scalar reward dispatch.
The repaired evaluator inserts that axis explicitly. The batched
training implementation checks against the repaired scalar evaluator
at initialization. A separate branch enumeration checks each learned
output, silence and the fixed full-bank policy. Source banks, private
signals, costs and as-of-fit reward labels are identical between plans.
