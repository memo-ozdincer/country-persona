# Source-quoted native comparison on 2744

Keep the six frozen-writer inputs, 128 generated tokens, 40-word
comparison limit, 160-word final limit, greedy decoding and fixed
routing policies. Change only the system instruction. Ask for short
exact operative phrases from both sources embedded in the comparison.
Give no selected spans and no sample answers. Generate all six pairs,
including crossed controls. The frozen source gate remains in force
in the admitted arm. Keep ungated scores as a diagnostic.

Judge against the existing source and relationship criteria before
scoring policies. Track whether each comparison quotes the two sources
exactly and whether the admitted record earns both relationship bonuses.
The success condition for this development run is a learned team score
above the reoptimized arrival-only policy under the same writer. The
data, routing reward bank and same-assistant grading remain exposed.

The GPU pool was occupied at launch preparation. Use a single
12-thread CPU process with the same BF16 and greedy settings. Replay
all six unchanged generic prompts on that CPU in the same run to
check the archived GPU comparator. Retain any differences.
