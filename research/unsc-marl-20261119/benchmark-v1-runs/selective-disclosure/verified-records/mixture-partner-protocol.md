# Use a mixture model when the archived opener is partly familiar

After inspecting the original unknown-partner results, add a convex
library model. It assigns a uniform prior over 21 mixtures from
0 to 1 in steps of 0.05. Each mixture describes independent
per-turn use of the two original conventions. Infer weights from
the same public receipts. On a history supported by either pure
rule, preserve the two-rule posterior. When both pure rules are
excluded and every observed symbol has support within the mixture,
use the convex forecast. For a changed action, require forecast
value at least as good as the equal-library action at both ends of
the central 80% posterior interval. If a receipt is impossible for
both library rules, back off to the direct action-value fit.

Include asymmetric 20/80 and 80/20 turn-wise mixtures. These were
outside the original experiment. Retain all prior held profiles,
grids, cap, messages and metrics. Use the same deterministic
sampling procedure and history sizes, with the expanded outcome
roster. These are cross-play comparisons using synthetic archival
histories. No true hidden card or current reward enters selection.
