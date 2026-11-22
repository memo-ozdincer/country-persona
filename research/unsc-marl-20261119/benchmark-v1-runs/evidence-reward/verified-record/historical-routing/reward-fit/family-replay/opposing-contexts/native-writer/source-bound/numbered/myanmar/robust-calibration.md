# Select routing under a one-criterion uncertainty interval

Treat the reviewed pair score as uncertain by one 7-point criterion.
Use the singleton scores and three possible pair grades spanning that
interval. Generate frozen dense, sparse, fixed and silent candidate
policies under each forecast. Evaluate every candidate over all three
forecasts. Require it to match the forecast documentary quality of
optimized silence at every grade where possible. Among eligible
candidates, maximize the worst net margin against the optimized
fixed-or-silent continuation for each forecast. If that quality set is
empty, maximize the worst documentary shortfall first, then the same
net margin. Select without the true bank. Score the selected policy and
the original point-estimate selector on the true held bank afterward.

Apply identical logic to the intact-record Myanmar bank and the prior
numbered UNIFIL bank. For each true bank, independently inject −7, 0,
or +7 at the review boundary and apply the method across the three
stipulated inventory priors. The choice of interval is fixed for this
ablation. Candidate action maps include the original point-estimate
options. No parameters are updated.
