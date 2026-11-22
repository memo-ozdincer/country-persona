# Learn the routing mode from delivered receipts

The controller chooses among four frozen pairs of local chair and responder policies. It updates its channel beliefs from the opening and final receipt masks and the policy used. The chair receives no grounding verdict for a dropped message, reward label, hidden card or public declaration of the true mode. Its four hypotheses are authored and exclude the measured Resolution 2593 rejection matrix. The 4% belief reset allows for changes. The active variant reserves every eighth episode for the policy expected to yield the most information. Probes use the same opening and are charged their own delivery costs. [Locked protocol](protocol.md) · [Implementation](../facilitator_channel_online.py)

| Resolution 2593, uniform inventories | Greedy receipt learning | Learning with probes | Fixed independent | Fixed clean fit | Oracle in the same menu |
| --- | ---: | ---: | ---: | ---: | ---: |
| Stable source-only replies | 59.313 | 59.303 | 58.562 | 59.325 | 59.342 |
| Stable question-visible replies | 57.573 | 57.365 | 58.562 | 52.957 | 58.562 |
| Clean → noisy → clean | 58.664 | 58.526 | 58.562 | 57.202 | 59.082 |

These are mean net objectives over 144 episodes and 128 paired replications, using a single seed. The training-fitted policy and the initial rule both appear in the menu. The oracle uses the actual condition only to expose the best choice in that menu. [All scores, posterior traces and phase values](results.json)

Under correlated inventories on Resolution 2593, the greedy policy never asks and stays at its initial 25% clean posterior. The receipt distributions for independent delivery are identical in the measured source-only and question-visible modes, under both priors. The clean fitted policy separates these modes by 0.309 total variation with uniform inventories and 0.266 with correlated inventories. Asking therefore supplies information. It also risks an unusable reply. Probe-based learning adds 0.039 points over independence in stable clean correlated episodes and loses 0.646 in stable noisy correlated episodes.

Across the four archived banks, periodic probes recover 0.067 points over independence in clean conditions. They lose 0.136 in the simulated fallback-loss condition and 0.198 under simulated topic asymmetry. The greedy controller matches independence on those archives. On the measured uniform switch schedule, greedy learning beats independence by 0.102 points and remains 0.418 below the oracle in the same menu. That gain does not carry to the correlated switch schedule. The authored hypotheses hold silence reliably admissible, while the topic-asymmetry stress channel also alters silent replies. This is a channel-model mismatch included in the test. All experiment episodes reuse frozen documentary rewards and cached or simulated dispositions. They provide evidence about adaptation to unreliable evidence delivery, with no additional generated discussions.

## Replay

From `benchmark-kit/reader-use`, use the project Python environment.

```sh
OPENBLAS_NUM_THREADS=1 python facilitator_channel_online.py facilitator-channel-fit-evidence/results.json
```
