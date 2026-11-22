# Public context and the learned policy

Replay the previously exposed six-option grid under four role observation modes. The full mode shows every public disclosure to the selected delegate. The one- and two-peer-turn modes retain every prior disclosure by that delegate and only the latest one or two disclosures by its peer. The compact mode sends two acceptance masks keyed by role and one shared mask of excluded packages. The original public ledger and six-slot budget are fixed across modes, and it always verifies outcomes with all admitted claims. Neither role receives the other's private menu.

The current policy looks up its own and the peer's acceptances and the union of prior exclusions. Speaker attribution of exclusions remains in the audit ledger and is available to the final record. Within routing, merging the two exclusion masks preserves all of the fields that drive the choice. The study also asserts identical actions, recipients, signs and stopping time between compact and full modes on every policy path.

| Actor-visible public context | Script agreements /34,434 | Learned agreements /34,434 | Script impasses /2,430 | Learned impasses /2,430 |
|---|---:|---:|---:|---:|
| Full history | 34,434 | 34,434 | 1,920 | 2,430 |
| One recent peer disclosure | 26,828 | 26,828 | 1,014 | 1,014 |
| Two recent peer disclosures | 31,620 | 31,620 | 1,240 | 1,608 |
| Compact summary | 34,434 | 34,434 | 1,920 | 2,430 |

With one recent peer disclosure, the learned policy issued 1,198 redundant exclusions over the disjoint presentations, versus zero with the compact view. These exclusions were truthful but had already been signed by the peer and therefore added no evidence. Counting all turns or all new role-assertions would not capture that loss. The same conclusion applies to agreements, with 7,974 redundant exclusions in the one-peer-disclosure condition. The compact summary is sufficient for this masked-set policy and the exact proof rule used here. The result does not test compression of natural-language explanations or Qwen input prompts. [Metrics](evidence/metrics.json) · [Replay](evidence/replay.json)
