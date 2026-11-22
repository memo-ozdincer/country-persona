# Fit recipient action rankings from counterfactual team rewards

Use the same development grids, unchanged opening rule and six
presentation orders for source-linked transfer. The previous recipient
fit predicted absolute certification scores. Now optimize the sign of
within-state payoff differences. Weight action pairs by their exact
reward gap and the occurrence probability of their local state. Retain
the uniform forecast and learn only a residual difference. Fit for
160 CPU Adam updates at 0.03, temperature 0.04 and L2 strength 0.02.
Exclude exact payoff ties from the loss.

Compare forced decisions against the previous reward regression,
uniform forecast, exact fixed-opener recipient and full exact team
bounds. Include a fixed safety check that rejects a learned override
if the forecast's predicted opportunity cost exceeds 0.02. Record
action override mass, net wins and losses by grid and the same
language projection and prior stress. No reserved actions or scores
are used to fit or choose the check.
