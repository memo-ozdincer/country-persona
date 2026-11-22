# Learn two send decisions from the Resolution 2664 terminal reward

Two desks independently choose whether to send their own source. A sent
source arrives independently with public probability p. The writer's order
is sampled after both decisions. Both desks know the deployment probability
of India-first presentation, but neither sees the realized order when acting.
When both cards arrive, the terminal score comes from the matching saved
writer output. Other outcomes use the saved scores under the same receipt
deletions. Neither writer nor wording changes during the replay.

Charge a send its expected standalone gain plus two points, using the
observed source-preserving standalone scale. This constructed opportunity
cost makes sending alone cost two points in expectation. A joint send is
optimal only when the source relationship's expected value exceeds four.
Keep the cost rule identical across learners and controls. Publish factual
release and cost-adjusted utility separately.

Use one fixed 64-episode exploratory log with p=0.90, balanced randomized
writer order, and independent 0.5 send probabilities. Each model uses the
same observed transitions and a least-squares terminal critic. Fit an
additive shared-return critic, a critic that can learn pair value but pools
writer order, and a critic that conditions pair value on the observed order.
Fit a fourth critic to exact per-receipt deletion scores, including zero-card
scores only as a public baseline. Log its extra reward lookups. The receipt
and writer order are observed only after the send decisions. At deployment
integrate over delivery and order, take the best joint action under the
critic, and give each desk its own deterministic action for that public
context. This is a model-based cooperative policy with centralized training
and a shared public context.

Evaluate exact expected utility, scores, and regret against each fixed send
policy and the exhaustive oracle. Hold out delivery probabilities
0.65, 0.75, 0.85, 0.95 and writer mixes 0.10, 0.50, 0.90. The balanced mix is
seen in training and serves as the delivery-only control. The other mixes
shift both. This simulation uses assistant-graded rewards on one exposed
docket. It tests observability and credit assignment without generating
additional text or tuning a backbone.
