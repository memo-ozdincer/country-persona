# Refit the two-desk sender critic after changing the chair

Use the same 64 exploratory actions, simulated deliveries and order draws as the
2664 sender fit, including its one fixed seed. Replace only the terminal score
with the newly measured target reward for that delivery mask and order. Refit
the additive, pair-pooled, and order-aware critics from those scalar grades.
Compare the frozen 2664 critic's policy and the target refits on the same 12
held transport settings, with the same cost and target scoring as the
previous 2739 transfer experiment. Report factual release and utility
separately. Grading comes from the seven matched generation calls. The
64 episodes reuse that finite archive and never request another model call.
