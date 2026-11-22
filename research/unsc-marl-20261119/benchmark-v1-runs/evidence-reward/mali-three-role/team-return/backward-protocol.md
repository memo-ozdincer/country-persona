# Learn from sampled replies before fitting early questions

The initial simultaneous policy-gradient run learned to stop at the first
turn. Retain that run and change credit assignment plus training exposure.
Fit three horizons backward. Sample random reachable public prefixes
independently of the current policies. At each horizon, sample the gain
from truthful signing versus withholding against the same lower-horizon
policy and shared future randomness. Fit the local delegate against that
gain. Then fit the chair from rollouts of asking with the fitted delegate
against stopping. Fit all returns from sampled trajectories with no exact
planner labels. Use the same observations, fee, held menu split and
evaluation profiles. Freeze a single seed and 12,288 sampled rows per
actor per stage. Use deterministic random-feature ridge regression to fit
the sampled differences. This tests the combined change. It does not
isolate prefix resets from backward credit assignment.
