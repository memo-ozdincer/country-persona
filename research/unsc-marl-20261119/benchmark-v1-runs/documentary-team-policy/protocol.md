# Learn both desks from terminal documentary reward

Use the archived exact-record scores and indexed witness verdicts for three
document views per docket. The first desk receives a private documentary
view. It can forward the view or stay silent. The second desk receives the
frozen verified claim bit only when the view arrives, or a missing-message
symbol otherwise. It chooses one of the two previously scored replies.
Each agent sees the docket. The first also sees the two delivery rates
and the forwarding price. The second cannot see the first desk's private
view. Its reply always attempts delivery under the declared rate. Use
the deterministic source renderer's record score minus the first desk's
stated price if it sends. Prices are artificial point costs.

Learn two Bernoulli actors by on-policy REINFORCE with shared final scalar
reward. The first actor has one logistic row per private view. The row
uses delivery rates, their product, and cost. The second actor has one
logit per docket and observation. Use one fixed seed, 512 updates and
256 episodes per update. A running reward mean from prior batches serves
as a baseline. No true source class, action advantage, per-actor reward
or counterfactual target enters the actor update. Compare greedy policies
under the initial and fitted parameters and with explicit fixed policies.

Hold out the listed transport rates, forwarding costs and two skewed
priors over the three views. Enumerate all transport branches for exact
expectations. The exact best policy under the same observation interface
enumerates all eight receiver mappings and computes the best sender
decision per view. Also cross the learned sender with a fixed partner
to see how reliance on the trained reader affects reward.

The test learns two policies in an archival cooperative environment.
The private view catalog, renderer, and frozen claim observations were
authored or reviewed on exposed dockets. Model weights and benchmark
release remain frozen. The test does not measure new utterance quality.
