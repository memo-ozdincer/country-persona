# Jointly fit send and reply heads under calibration error

The frozen interval selector often loses to fixed routing on held
synthetic score banks. Fit one new pair of small routing heads on the
same 144 synthetic banks used by the sparse fit. Use the original three
inventory laws. Give the router and responder the singleton bank plus
one reviewed pair forecast, with the same three possible grade offsets
as the shift audit. Optimize the two heads together on actual net
released points from the synthetic bank. The true grade vector comes
into the gradient through the shared reward, while router and responder
features use only the observed forecast. Keep opening actions fixed
under the singleton bank. Use the base head architecture, optimizer,
temperature schedules and 120-update budget.

Evaluate on the sealed 360-condition shift matrix. Compare the
original candidate set with the one obtained by replacing its dense
head with the new fit. The sparse and scripted candidates, pruning,
review budget and selection rule stay the same. Report separate
results for the historical and synthetic suites. The new variant is
a single transfer test. It does not revise the prior held-bank
inclusion rules or declare a deployment winner using held rewards.
