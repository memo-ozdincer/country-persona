# Learn forecast corrections from paired outcomes

The first rollout fit hurt net mainly by changing responder action
values, including actions whose score was already observed. Keep the
existing decentralized no-fit actor logic and learn corrections only
for receipt mask 3, whose review may be wrong, and mask 7, whose score
is inferred. In each sampled transition compare legal replies with
silence under the same score bank and delivery. Fit the reward
prediction error from those differences. Costs cancel from this
residual because the observed and predicted alternatives pay the
same fees. No planner actions are training labels.

Train a small shift-invariant linear model on the first 36 locked
synthetic banks and their three laws and review offsets. Use the
remaining 12 synthetic banks to select a correction strength from
0, 0.25, 0.5 and 1 by modeled net on that validation split. This is a
fresh fit and one predetermined finite coefficient choice. Keep held
historical rows outside fitting and selection. Reuse the existing
three-stage no-fit actor construction in validation and deployment.
Keep all other scores and openings unchanged. Compare the selected
and full-strength corrections with no-fit and the matched fixed and
informed references on all 90 held conditions.
