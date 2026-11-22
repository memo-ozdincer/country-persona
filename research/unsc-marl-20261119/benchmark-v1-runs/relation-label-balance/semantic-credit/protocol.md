# Use frozen source representations for corrective replies

Reuse the 27 exact claims and the identity and both cyclic readings.
Replay their existing prompts on one Aurora model revision. Capture
the three native label logits and a 32-dimensional fixed Gaussian
projection of the final prompt hidden state. The projection is seeded
before collection and scaled by the hidden vector norm. The responses
still use the same constrained label menu. Capture 81 short reads.

Compare two staged fits on the same new logits and same legal actions,
payoff, and .10 query cost. Fit each reviewer from the exact expected
payoff over legal actions on both cyclic views. The control uses the
existing margin and agreement features. The intervention appends six
principal components of the projected reviewer state, fitted and scaled
using only the training families. Fit the proposer against that frozen
reviewer, keeping the proposer's original features. Both heads receive
160 exact updates at step size .2 and L2 .02. Fit four archive
leave-family-out folds and a four-family-to-Myanmar transfer. Report
greedy and stochastic net, decisions, query use, first read, fixed
confidence controls and the request ceiling with each reviewer
frozen. Check zero gold access in inference and preserve all negative
outcomes. All cases have prior exposure. This is a frozen representation
study, with no Qwen weight updates or new judging.
