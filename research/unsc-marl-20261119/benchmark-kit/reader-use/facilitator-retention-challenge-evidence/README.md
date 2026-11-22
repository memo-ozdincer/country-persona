# Challenge the first judge's positive decisions

The first gate admits nine of 14 distinct Resolution 2504 drafts under the chronology rubric. Five pass the prior exact-span review and four fail. The second pass uses the same frozen Qwen3.5-4B with a different prompt to find a missing requirement or material error. It sees each of the nine drafts, the authorized source and the chronology rubric. Only a literal CLEAR verdict preserves first-gate approval. The prompt was authored after inspecting first-stage errors on this case. [Repair protocol](protocol.md) · [First gate results](../facilitator-retention-judge-evidence/README.md)

The second pass removes all four false approvals and rejects two of the five reviewed passes. It catches the missing vote-threshold explanation and the drafts with incorrect procedural claims or false statements about the contents of the source. Its two false rejections cite the request to adopt the penholders' text and the Russian withdrawal after adoption, even though those details are explicitly available in their respective drafts. The nine challenge calls use 3,549 input and 88 generated tokens. All verdicts parse. [Raw verdicts](final-records.json) · [Combined decisions and replay](replay.json)

| Chronology-scored ideal-trained policy | Uniform net | Correlated net |
| --- | ---: | ---: |
| Reviewed-label selector | 58.898 | 55.486 |
| Automatic first pass, reviewed credit | 58.857 | 51.489 |
| Two passes, reviewed credit | 55.501 | 55.447 |
| Two-pass gain over the best no-request team using the same gate | −0.223 | +3.487 |

The first pass falsely prioritizes the generic procedural draft. The challenge lets a valid topical draft replace it, recovering 3.959 net points under correlated inventories. Rejecting the two sound drafts costs 3.356 points under uniform inventories. The modeled probability of a reviewed-incomplete card reaching the recorder becomes zero under both priors on this replay. The ideal-trained policy averages 3.20 and 3.15 judge calls per episode without caching, up from 1.75. The cost is additional to draft generation. This repair uses a single examined event and same-assistant reference annotations. The numbers establish a precision–recall and routing tradeoff on this set. [Expected call counts and audited policy outcomes](replay.json)

## Reproduce from the parent directory

```sh
export PYTHONPATH="$(git rev-parse --show-toplevel)/src"
export OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
python facilitator_retention_challenge.py score facilitator-retention-challenge-evidence
python facilitator_retention_challenge_replay.py
```
