# Train on both sides of the follow-up delivery threshold

Keep the first signed stage, terminal training paths, role features,
two heads, initialization, cost, reward, update count and optimizer
fixed. Replay each synthetic terminal path at follow-up delivery
probabilities 0.10, 0.16, 0.24, 0.32, 0.45, 0.65 and 0.90 with equal
weight per rate. This changes second-stage delivery during training
only. Reuse the original held presentations with first-stage
delivery unchanged. Evaluate the original and newly fitted teams
at 0.12, 0.20, 0.275, 0.28, 0.285, 0.35, 0.55, 0.80 and 0.95.
Compare greedy actions with the exact cost-aware policy, including
question and send cost, delivered coverage and net return. Below
0.28 any question aimed at completing the record has negative
expected net value. At 0.28 prefer silence in ties. Report erroneous
queries and missed coverage together.
