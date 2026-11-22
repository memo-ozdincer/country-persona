# Can the delisting team learn from one realized terminal score?

The earlier Resolution 2744 native reward fit queried both send and withhold
for the same episode. Here each episode draws one private view, price and
delivery setting, takes one joint action, and observes one resulting score.
Use the released compact-writer bank and the same held delivery rates, priors
and fees as the paired-credit experiment. Only simulated episodes are new.

Compare shared-reward REINFORCE with a centralized receipt-value estimator
and decentralized execution. The estimator uses the receipt IDs recorded by
the environment and the observed score for that receipt. It learns
the values of public-only, single-delivery and double-delivery records.
The two information conditions give the reply policy either arrival alone
or the archived semantic observation. Both actors know the delivery model
and price. Their actions may depend only on their local view. The estimator
can optimize a different local policy at each public setting. This stronger
inductive bias and its extra training metadata are part of the intervention.

Use one fixed seed and common exogenous draws across arms. Save snapshots
after 64, 256, 1024 and 8192 terminal observations. Include exact controls
with the known typed rubric and reviewed native scoring. Freeze policies
learned on the compact writer when comparing with the gated and topic-guided
writers. Report results per bank and without pooling the checkpoints.
At test time no actor gets terminal feedback.
