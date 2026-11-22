# Condition the second sender on the first received passage

Use the same three-role selection menus, documentary values,
partner forecasts and independent receipt probabilities as the
prior CPU fit. One desk chooses last. It may inspect the exact
selection sent by the second desk if that note reaches the chair.
An empty observation means that the note did not arrive. The
third desk's choice and all other deliveries are hidden. The
simulation uses the same delivered second note for observation
and scoring. Broadcasting this receipt is treated as free.

Train the same three shared coefficients from the exact expected
team return over actions and receipts. Use 96 synthetic cases and
150 updates under the previous seeds and rate. No archived UN
case or policy label enters training. Keep 48 separately generated
cases for evaluation. The earlier no-observation fit is the
matched open-loop control. Check that the same policy without
observation computes the earlier optimizer's objective and
gradient. Also test the new weights on the open-loop inputs.

Compare local-only selection, receipt-conditioned announced
priority, and a receipt-only control that observes arrival
without observing passage IDs. Compute exact adaptive and static
oracles with access to the true tables. Score the two archived UN
menus separately at four prespecified delivery rates. The
documentary return comes from the existing case renderers for
each joint selection and receipt set. Report release and avoid
attributing interaction gains to the fit when equally informed
rules achieve them. This is a simulated observation-boundary
experiment on authored structured inputs. It uses no new LLM
calls or world data.
