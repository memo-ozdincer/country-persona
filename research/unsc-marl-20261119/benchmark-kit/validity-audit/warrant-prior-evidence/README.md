# Learn inventory correlations from public workshop receipts

The preceding experiment gave planners the distribution of private grade cards. This follow-up keeps the same learned opening weights, decision semantics and receipt certificate. It hides the inventory distribution and supplies only the authorized grade disclosures from earlier simulated calibration episodes. Every nine episodes cover all nine slot pairs, and the 10% link losses still apply. Learners integrate over all full worlds compatible with each partial disclosure. The evaluation uses the 32 previously drawn synthetic domains, fresh latent correlations and fresh calibration samples from one seed. [Frozen protocol](protocol.md) · [Likelihood and planning code](../warrant_prior_learning.py)

The constrained estimator averages 24 one-to-one association hypotheses and an independence hypothesis. Its coupled mass is 60%, while the actual matching condition uses 65%. A second learner uses EM with a two-count symmetric prior and permits any joint table. The mixed condition combines two unknown matches and lies outside the single-match model. The oracle columns get the true prior and keep the same opening weights. The true-prior end-to-end column is a comparator, since it does not optimize the weights for each test domain. The certificate checks all public worlds and uses no learned probability to discard a feasible world.

## Results

| Inventory condition | Uniform planner | Matching learner, 81 calibration episodes | Matching learner, requests only | True-prior planner |
| --- | ---: | ---: | ---: | ---: |
| Independent | 0.919815 | 0.918771 | 0.919815 | 0.919815 |
| Hidden one-to-one match | 0.919702 | 0.925133 | 0.923821 | 0.925133 |
| Hidden mixture of two matches | 0.920553 | 0.921859 | 0.922488 | 0.923973 |

These scores average net certified decisions over 32 domains. Net subtracts the usual deployment follow-up charges. The constrained learner matches the mean true-prior planner score on the single-match condition with 81 calibration episodes. Against uniform planning, it wins nine domains, loses one and ties 22. In the mixture, keeping the openings fixed captures a larger gain than replanning both openings, and avoids a loss under independence. At 27 samples the unconstrained model briefly leads on the mixed condition. Neither model gives a consistent monotone improvement with more reports. [All calibration receipts and domain outcomes](results.json) · [Aggregate audit](audit.json)

Calibration overhead is outside those net scores. Each calibration episode takes two attempted disclosures. At an illustrative charge of 0.10 points per attempt, the 81-episode constrained learner costs 16.2 points. Its mean gain of 0.005432 on one-to-one matching needs about 2,983 scored workshops at that gain to break even. That calculation assumes a stationary prior, the same future case mixture and no additional annotation cost. If the reports are already available from ordinary workshops, the incremental collection cost can be lower. Use the high observation cost here to keep narrow simulator gains in context.

The audit reconstructs all 576 learned prior tables from the public grade ledger without using hidden inventory identities. This is new learning about a shared environment, using previously trained local actors. It does not provide evidence about naturally occurring national preferences, free-form deliberation, or independent final-record judgments.

## Replay

Use the project model Python environment from `benchmark-kit/validity-audit`.

```sh
OPENBLAS_NUM_THREADS=1 python warrant_prior_learning.py trained-warrant-evidence/results.json
OPENBLAS_NUM_THREADS=1 python warrant_prior_audit.py warrant-prior-evidence/results.json
```
