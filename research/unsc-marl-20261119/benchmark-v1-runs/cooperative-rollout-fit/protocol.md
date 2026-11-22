# Fit decentralized routing from sampled shared returns

Train a responder and a chair in the existing evidence relay. They can
attempt a truthful card transmission or stay silent. Opening policies,
delivery probabilities, action costs and released-record reward stay
fixed. The chair acts from the public receipt mask. The responder acts
from its own inventory, previous send and heard request.

At each update sample hidden desk inventories and four delivery bits.
Evaluate a legal alternative and silence with the same inventory and
delivery draws. Their difference removes the pre-action reward and
charges the transmission even when delivery fails. Fit a low-dimensional
residual to the forecast-based value of each role's actions. The fitted
targets come from realized shared returns, with no oracle action labels.
Fit the responder first, then the chair against that responder. Repeat
for three rounds. A frozen initial chair comes from estimated effects and
a scripted responder. Reward-aware residual weights are the only learned
parameters. A zero-weight implementation gives a matched no-fit control.

Fit on the first 48 distinct banks of the existing sparse synthetic
corpus, under its three base inventory laws. The opening learner sees
public-only and three singleton grades. Continuation sees seven grades
with the mask-3 review perturbed by -7, 0 or +7. Infer the full-receipt
grade using the existing forecast. The actual reward bank appears only
in the simulator's return and held evaluation. Sample 192 transitions
per training context and round. Use one seed and fixed ridge penalties.
Give the responder's announced-context posterior a 10% uniform-legal
request component to price counterfactual queries. The actual deployed
chair is deterministic after the weight update. Reuse the same posterior
in the no-fit policy.

Evaluate the five historical banks and 90 conditions of the archived
cross-case matrix. None of those banks may match any training bank
after an additive score shift. Preserve the earlier opening and prior
information budget for all comparisons. Compare the learned policy,
matched zero-weight policy, fixed targeting and exact adaptive search
under the announced forecast. Give the informed fixed and exact adaptive
references the true mixture and score bank, with the same openings.
Report released score, net reward, request rate and loss to informed
silence separately. The historical records are exposed documentary
surfaces. This fit measures protocol learning in the simulated channel.
