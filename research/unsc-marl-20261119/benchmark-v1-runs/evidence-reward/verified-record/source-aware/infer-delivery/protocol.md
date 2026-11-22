# Estimate delivery from public workshop traces

Freeze both learned teams at the nominal rates used in the earlier
selector. Assume the same unknown channel profile across a campaign of
24 independent workshops, each with a fresh uniform private world.
Use a fixed 64-point grid, four possible delivery rates per desk,
and an independent prior centred on the nominal report. Choose a
team or silence before each workshop using all earlier public traces.
Keep that team's chair and sending rule fixed inside the workshop.

Update the rate belief from the probability of the entire public
trace. A sign reveals its bit, requires a sender who would attempt
that sign and counts as a delivery. With no sign, marginalize over
unknown private bits and both causes, optional silence and channel
loss. The verifier has separate access to the hidden draws, but the
estimator accesses only the selected policy and the public trace.

Compare nominal selection, initial prior without updating,
a naive update that models every question as a send, and correctly
conditioning on the gate. Also compare a paid preflight ping for
each desk, followed by the same correct update. A ping forces a send
and costs the ordinary question plus reply fee. Include the
previous three delivery shifts and a stable high-delivery control.
Use paired draws across all modes and one fixed seed with 512
campaigns per condition, budgets two and three, and the three
existing source packets. Use frozen final scoring for every payoff.
The hindsight reference can choose either frozen pair or silence
under the true delivery law. It has no access to particular
private worlds or future receipt draws.
