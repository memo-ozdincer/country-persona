# Use source IDs for the Haiti documentary replies

The prior [Resolution 2699 preflight](../facilitator-preflight-2699-evidence/README.md) recovered speaker attribution with source-only writing, yet admitted only the China card. This test keeps physical routing, authorization and final-record scoring fixed. It asks Qwen3.5-4B to select source sentence IDs for three requested claims per delegation. The model sees an attributed deck of documentary sentences and the requested claims. It returns three letters and uses X when a claim is unavailable. The receiver uses an author-verified mapping from source IDs to immutable sentences, rather than trusting generated paraphrases. [Frozen decks and expected mappings](decks.json) · [Locked protocol](protocol.md)

The full and source-withheld decks run in two different menu orders. The unsupported-claim foils preserve all original evidence and change the requested claim. One foil asks the model to find the erroneous Russia proposition that the Council should approve the concept of operations before receiving it. The relevant deck says that Russia sought substantive approval instead of presentation after the fact. One available, overlapping source sentence can therefore be the wrong citation. The selector and its controls preserve the original claim's actor and scope. Full documentary payloads are admitted under the primary replay only if both reads establish all three claims. [Runnable selection and replay](../facilitator_cited_2699.py) · [Scoring logic](../facilitator_cited_2699_score.py)

## Results

All 15 calls return valid syntax. The model selects 15 of 18 expected IDs on full decks. Four of six complete-deck reads match every field. The first order admits China and Russia, the second admits Ecuador and Russia, and the primary double-read rule admits only Russia. On withheld targets, the model falsely cites a sentence in five of six calls. It also falsely cites a sentence on two of three unsupported-claim foils, including approval before receipt. Across both orders it selects the same irrelevant source sentence for the withheld Ecuador and China targets. The two findings persist after decoding letters back to their underlying statements. [Exact IDs and selected sentences](results.json)

| Fitted router reply interface | Uniform net | Correlated net |
| --- | ---: | ---: |
| Visible-question free prose | 52.667 | 50.708 |
| Source-only free prose | 56.031 | 51.514 |
| Source IDs, first order | 59.210 | 56.696 |
| Source IDs, second order | 55.567 | 55.958 |
| Source IDs, both orders required | 55.452 | 55.833 |
| Source IDs, verified merge across orders | 59.325 | 56.821 |

The replay uses the prior English query outputs, four binary link events, the same authorized cards and the same renderer. Net adds completion credit and charges attempted messages. The batch uses 4,018 input and 60 output tokens across all 15 calls. The generation budget and costs of preparing the verified registry are separate from message charges.

The verified merge is a post hoc alternative to the double-read rule. It takes a claim only if a selected ID matches an author-verified claim-to-source mapping, and combines valid witnesses across reads. It recovers all three documentary cards, rejects all seven erroneous citations from the controls, and exactly reproduces typed transport. Under this complete registry, the fitted router beats independent delivery by 0.763 and 0.315 net points. It trails the initial weights by 0.017 on uniform inventories and improves on them by 0.299 on correlated inventories. Since the receiver already has the verified mappings, deterministic forwarding is a valid baseline and avoids the selection calls. The experiment verifies a guarded transport mechanism on the exposed dossier. Model citations alone fail the missing-evidence and legal-timing controls. [Verified merge, rejected citations and route scores](union.json)

## Replay

Use the project Python environment from `benchmark-kit/reader-use`.

```sh
python facilitator_cited_2699.py verify facilitator-cited-2699-evidence
python facilitator_cited_2699_score.py facilitator-cited-2699-evidence
python facilitator_cited_2699_union.py facilitator-cited-2699-evidence/results.json
```
