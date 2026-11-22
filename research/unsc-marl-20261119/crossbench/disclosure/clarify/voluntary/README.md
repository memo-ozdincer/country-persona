# Learning when to volunteer a signed claim

Question: can reinforcement learning improve over a simple role-local disclosure policy under the exact same four-call budget? The public query planner is a protocol comparator; the greedy local script is the learning comparator.

The two role agents share parameters. Each receives its own compatibility menu and signed claims plus the public peer claims. Its action selects a package and the environment discloses the truthful sign. The environment stops the episode when the public ledger can certify a result. Under fixed alternating roles, a role acts at most twice. The policy starts with the local-script action priority and learns a small residual. Each training reward is a unit certificate minus 0.025 per continuation slot, with no reward for individual exclusions. Training uses only balanced simulated three-option presentations. The held-out four-option grid is scored exhaustively by decision class, for the initialized policy, the trained policy, and the same trained policy with public peer signs masked at action time.

The measurement compares action selection under already structured and trusted private facts. Historical persona fidelity, natural-language parsing and the final decision memo need separate evidence.

Before fitting, an exhaustive software audit of the 24 fixed local priority orders found a stronger initialization on the four-option grid. It favors matching a peer's acceptance, then excluding an option the peer has not accepted, then offering a new acceptance, and finally excluding a peer acceptance. It certifies 916/916 agreements and 72/108 impasses. This is a tuned scripted control selected on the grid, so the four-option results will test transfer of the weight updates and are development evidence for the complete system. The learned residual must improve on this control, rather than merely beating the original 856/916 script. [Priority audit](../priority-audit.json)

## Result

| Four-option policy | Agreement /916 | Impasse /108 | Mean continuation slots | Mean terminal reward |
|---|---:|---:|---:|---:|
| Tuned script at initialization | 916 | 72 | 1.395 | 0.9300 |
| Reinforcement-learned residual | 898 | 72 | 1.412 | 0.9120 |
| Learned residual with peer signs masked | 594 | 40 | 2.706 | 0.5515 |

The residual received 160 CPU updates. It recovered no new certificates and lost 18 agreements. In every lost agreement the first action difference was on continuation two. The script offered an option the peer had not yet addressed, while the learned policy excluded an option the peer had accepted. The outcomes and first-certificate turns of the remaining 1,006 presentations were identical. The visibility ablation shows the fitted policy depends on peer evidence. It does not show an improvement caused by training, since the untrained comparator also uses peer evidence.

The selected initialization and fitted policy both miss 12 impasses that are reachable under the alternating schedule and 24 prohibited by the two-slots-per-role capacity. Three-option training and this one-seed residual have not improved the four-option development benchmark. Future policy tests should preserve the stronger scripted agreement behavior and target the reachable impasse cases. [Raw scored traces](evidence/results.json) · [Updates](evidence/updates.jsonl) · [Replay](evidence/replay.json)

## Post-fit scripted diagnosis

The 12 reachable impasses missed by the script all have two compatible packages in the left mandate and one in the right mandate. This motivated one local change. If the first continuation speaker has a singleton menu, it tries to match the peer's acceptance first and, failing that, states its exclusion of that package before excluding an unaddressed option. All subsequent decisions use the tuned script. This restores exactly those 12 impasses and preserves all 916 agreements. It matches the full-information certification ceiling of 916 agreements and 84 impasses on this grid. This rule was chosen after inspecting the four-option errors, so the result is a development diagnostic. The remaining 24 impasses require a new routing or disclosure protocol under four slots. [Exact post-fit comparison](singleton-control.json)
