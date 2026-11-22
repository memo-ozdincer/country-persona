# Recover routing while screening comparisons after a writer change

Replay the studied Resolution 2744 candidate outputs. Fit during three
128-episode phases: compact writer, topic-guided writer, and a mixed
writer pool containing equal shares of both. A fresh independent writer
draw is made per rollout and its identity is hidden from both desks.
The change signal tells the learner to reset its routing estimates, but
gives it no information about the writer mix. Cache prior exact reviews
across phases. The archive supplies deterministic reference marks for
each exact candidate and source packet. The mixtures are simulated.

Run one peer-content and one arrival-only learner. Each starts with
source-only score estimates, and one provisional comparison estimate per
unvisited pair. Select routes using those estimates with the same fixed
exploration as the terminal-feedback experiment. In a rollout, review
only a genuinely received pair on the prior two-pair candidate list.
Until the review is available, release the source-only version of an
unseen candidate. On subsequent exact matches, include a comparison
only if the reviewed candidate improves that record. Bind cache entries
to both the exact record and its source prefix. The rollout's routing
update uses only its own released score and the corresponding observed
proposal score when the proposal is reviewed or hits the exact cache.

At each checkpoint freeze the policies and estimate expected held scores,
without adding reviews. Compare against optimized source-only routing, the
best screened route with known mixture and complete review, and a frozen
compact route with pair-level approvals. Report realized review counts and
released scores, failures, and mean expected held utility. In sensitivity
analysis charge one or five points per distinct shadow review. The
analysis excludes language-model and latency costs. Measure exploration
cost against the optimized source-only policy on matched exogenous draws. This tests routing and
release decisions under known transport and exact recurring text.

The exploration ablation caps deliberate exploration at 32 episodes per
phase. It continues updating from ordinary resulting receipts. Both variants
use the same review rule for any previously unreviewed candidate.
