# Select passage identifiers instead of retyping quotes

Run the same published 25 calibration anchors with the same Qwen
checkpoint, generation settings, and output cap as the verbatim-quote
baseline. Replace the quotation task with selecting identifiers from an
enumerated view of the same evidence. Keep the rubric, grading guidance,
status fields, and original validator. Use the same authored expected labels
only for evaluation.

Number each candidate, source block and turn by sentence. The model
supplies a span identifier or a same-text contiguous range in each quote
field. Bind chosen identifiers back to original text offsets. Keep status
predictions, criterion labels and reasons verbatim. An unknown identifier,
cross-source range or invalid verdict remains a failure. Strip a single
outer JSON fence before expansion so shell formatting does not hide a
citation problem. Do not infer, fill or revise citations or verdicts.

Report usable verdicts, label agreement and the false authorization guard
from the prior test. This is an adapter experiment on exposed anchors.
The distributed benchmark remains frozen.
