# Score complete messages before choosing semantic IDs

Reuse the same Somalia causal branch, model prompts, role menus,
compound U.S. unit, transport and final rubric. Enumerate every
distinct ordered selection, including the empty selection. For each
one, score the complete message and its end token for a finite set
of declared surface forms. Use string arrays, equivalent integer
arrays for decimal IDs, compact and ordinary whitespace, and each
array inside one JSON fence. Score every form with the unmasked
native model. Sum the probabilities of the finite representations
for each ordered selection. Choose the selection with maximum
summed probability and emit its canonical string array. Also log
the best choice under the canonical representation alone.

This decoder chooses a typed message before transport. Roles can
elect an empty message. This test compares full-string likelihood
with the greedy prefix decoder on the same scoped prompts. It uses
finite candidate scoring, four expected request contexts, and a
cap of 600 scored sequence forms across the run. The surface set,
tie behavior, case and metrics are frozen before checkpoint access.
