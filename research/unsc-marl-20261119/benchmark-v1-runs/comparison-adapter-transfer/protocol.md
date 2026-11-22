# Train comparison realization apart from diplomatic routing

Fit a small output-only Qwen3.5-4B rank-four adapter on decisions
from 2721 and 2664. Train explicit source-supported comparisons and
the exact NONE response where the supplied roles do not establish a
specific relation. Use authored paraphrases on the same training
dockets to vary evidence wording. Keep 2744 completely outside the
optimizer and the target text. Freeze the six original 2744
comparison prompts, rubric, gate, source record and routing policy
before optimization. Use the general prompt without the topic clue.
The family separation is experimental. The inherited 2744 outputs
were already examined in earlier trials.

Keep the frozen model baseline and adapted writer on the same
checkpoint, prompt tokens, device and greedy decoder. Train with
completion-only token loss for two passes over 12 examples. Align
next-token targets explicitly and record every update, frozen
parameter-version checks and exact probe equality after disk reload.
Generate all six held outputs with and without the adapter. Use
one semantic reader and the inherited source bindings to score the
same scenarios under the fixed jointly learned delivery-value policy
and matched optimized arrival-only control. This is an intervention
on the language writer that serves the MARL team. It does not retrain
the routing actors or change the closed benchmark.
