# Combine the fitted forecast with the verified pair review

Reuse the 23 archived triggering conditions and their admitted pair
scores from the final live review sequence. Use the same learned reward
weights and strength chosen on synthetic validation. Keep an admitted
pair score fixed in the primary combined policy, allowing the model
to correct the inferred score at mask 7. Compare against the same
learner that also adjusts the verified pair score, the no-fit policy
with the verified score, the learned policy on the original noisy
score, and the earlier reviewed adaptive search. No new reviews or
fit are involved.

Independently dispatch the archived learned policy and the selected
reward correction on all 90 held rows by exact transport branch
enumeration. Keep documentary and communication-cost results separate.
