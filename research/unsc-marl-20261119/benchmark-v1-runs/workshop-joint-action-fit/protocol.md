# Joint reward fit for a responder and a chair

Freeze Qwen3.5-4B and extract its last-token features and next-token score
for each allowed action from native prompts. Use a separate residual
matrix for each of two policies. The responder sees its own requirement,
the menu, and the fixed opening declaration and candidate. It can disclose
its own requirement, endorse the opening proposal, or withhold. The chair
sees only the menu and the two public messages. It can choose a package,
record impasse, or leave the decision unresolved. Action labels are single
letter tokens with an explicit mapping. No generated prose enters the
training reward.

Train both residuals for 64 full-batch updates on the exact expected shared
return summed across the three response branches. Use sixteen synthetic
workshops with distinct phrases, exhaustive pairs of two-valued conditions
and shuffled menu positions. Reward a certificate-supported correct
decision by one, give supported defer 0.15, penalize wrong decisions by
one, and penalize a false endorsement by one regardless of the chair.
Charge 0.04 to disclose and 0.02 to endorse. The ledger is the evaluation
oracle, with each responder's truth evaluated against its own mandate.

Run frozen Qwen, joint residuals, a matched featureless bias fit and exact
control with fixed disclosure. Hold both v1 UN families and all archived
notes out of fitting. Report greedy and expected metrics by family and
speaker order. Evaluate the chair separately on the four actual note
pairs from the Syria raw and constraint-only peer arms in each condition.
Their targets are the publicly supportable disposition and, separately,
the workshop key. This is a joint language-conditioned action-policy
fit. The opening is fixed, the response surface is finite and all
remaining generation and Qwen backbone weights are frozen.
