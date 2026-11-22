# Remove unnecessary requests from the fitted historical route

Freeze the just-fitted weights. At each iteration evaluate removing
one request from the public policy map. Recompute the learned
responder's public-mask posterior using the proposed map. Take the
highest strictly positive net change from any removal and repeat
until no removal improves net. Do not add or change requests and
do not fit parameters. The scoring model and inventory prior are
public assumptions. No individual hidden inventory is used.

Compare with the unpruned fit, the matched exact controls and a
version that prunes without updating the responder's expectation of
which question carries which information. Run on both historical
score banks and the same 108 synthetic holdout conditions. Keep
receipt probabilities and source compiler unchanged.
