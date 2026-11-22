# Attribute question and answer costs separately

The joint expected-reward fit asks in 104 of 120 held presentations
and sends 48 unnecessary answers. Its public planner counterpart
recovers the same expected proof mass in 80 questions, using an
exact responder. Train the existing responder residual directly to
distinguish branches that gain expected team reward from a verified
send over passing. Balance the two reward-sign classes over available
synthetic branches. Keep the 96-update budget.

Fit the chair's existing seven features to the signed counterfactual
advantage of each question relative to silence, using the fitted
responder's greedy policy. The chair still has only public features.
Evaluate both learned component swaps on the same held grid. Distinguish
agreement and impasse receipts, correct decisions and avoidable cost.
This is a dependent counterfactual-credit fit with no new model calls
or fitting on held populations.
