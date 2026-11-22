# Require a modeled payoff gain before switching recipients

In the completed all-view replay the rank switch only uses the
posterior majority: choose rank when balanced seems more likely.
Replace that choice with the existing expected-payoff comparison
of the fixed and learned recipients. Its estimates use the exact
workshop verifier, the two announced candidate priors and the
same previously observed histories. No released record score or
new outcome label is used for policy selection. Break ties toward
fixed.

Report the probability that this mode selects the learned policy
under each actual regime. Reuse every mechanically verified
record and identical receipt and fee weights. Compare its final
record and settled outcome against the already evaluated switch.
This replays a public-model selector, holding learned weights and
the final renderer fixed.
