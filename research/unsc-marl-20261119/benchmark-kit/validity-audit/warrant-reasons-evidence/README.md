# Distinguish feasible packages from winning packages in the final memo

The [live workshop](../warrant-live-evidence/README.md) recovered its intended decisions after authorization was enforced at the reporting boundary. Its final writer still incorrectly described B as its only feasible package. We keep the previous decision certificate and add a comparison table derived from exactly the same delivered grades. The table separately shows whether each package is feasible and best in all, some or none of the compatible card pairs, plus the grade ranges among its feasible pairs. The writer composes its own explanation. [Locked protocol](protocol.md) · [Package table and runner](../warrant_reasons.py)

The panel has four archived live-transport views and six typed views from every condition where the frozen learned and initial opening policies differed in net on the unfiltered evaluation. For each of those three conditions, the first branch with different permissible decisions supplies an initial and a fitted receipt view under the same cards and link events. These added views are new to the language writer. They isolate cases in which a change in routing could change the final decision. Their selection precludes interpreting the final scores as an overall trained-policy advantage.

Both arms receive the same source facts, public grade domains, correct decision certificate and 230-token output ceiling. The augmented arm gets the comparison table and a short instruction to use the feasibility and optimality columns separately. The memo remains capped at 90 words. Reviewers see opaque candidate IDs with the public proof facts and all relevant package properties. [Review rubric and exact-span scoring](../warrant_reasons_score.py)

## Results

| Views | Certificate only, correct decisions | Certificate + package table, correct decisions | Certificate only, release | Certificate + package table, release |
| --- | ---: | ---: | ---: | ---: |
| All ten rows | 10/10 | 7/10 | 5/10 | 3/10 |
| Eight distinct inputs per arm | 8/8 | 6/8 | 3/8 | 3/8 |
| Four archived live views | 4/4 | 4/4 | 1/4 | 2/4 |
| Four distinct additional typed views | 4/4 | 2/4 | 2/4 | 1/4 |

The table fixes the Mali explanation. The writer states that A remains feasible and B alone is the shared best decision. It also adds factual and decision errors on the additional views. In the duplicated impasse view it calls C feasible and prints UNRESOLVED while the certificate warrants IMPASSE and the table marks C infeasible in every compatible pair. In another view it takes variation in the tied winner set to mean no common winner, even though all four pairs rank B first or tied first. That output also has invalid JSON. [Opaque exact-span review](review.json) · [Per-candidate scoring](results.json)

The 20 calls include 16 distinct prompts. Two views in each arm repeat when uniform and correlated inventory assumptions produce the same receipt ledger and public warrant. Identical prompts receive the same reviewed labels. Deduplication changes the overall release comparison from a decline to a tie. The table still reduces decision accuracy on the distinct inputs and increases total input from 4,209 to 5,979 tokens over the ten rows. [Counts by group and deduplication rule](summary.json)

The exact routing audit covers every inventory and link outcome in the three policy-difference conditions. In domain 7 under uniform inventories, 1.42% of outcomes can be certified only by the initial policy and 0.91% only by the fit. The first differing branch favors the fit despite the overall loss. Report the full distribution when measuring learning. A selected branch reveals which proof reaches the writer. [Route audit](route-audit.json) · [Deterministic references from the same public evidence](reference.json)

## Replay

From `benchmark-kit/validity-audit`, use the project Python environment.

```sh
python warrant_reasons.py verify warrant-reasons-evidence
python warrant_reasons_score.py score warrant-reasons-evidence
python warrant_reasons_summary.py warrant-reasons-evidence
python warrant_reasons_route_audit.py
```
