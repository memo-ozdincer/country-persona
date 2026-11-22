# Let a model select the passages actually sent on Resolution 2466

The prospective budget replay assumed that choosing a desk delivered both of its reviewed source clauses. Here frozen Qwen3.5-4B selects passage IDs from its own desk cards, with either no question or a question about one of the three desks. The question supplies context. Each input carries its own two reviewable clauses and a public distractor. Three withheld-field controls remove a clause from its candidate set. The host forwards a clause only when its ID matches the locked field and was offered, and retains a valid field when its sibling fails. The host uses the actual source text. [Locked protocol](protocol.md) · [Case packet and provenance](../README.md)

The replay tracks six individual evidence fields. A received desk appears in the chair observation if at least one field was admitted. The learned controller and declared planners retain that coarse observation and stay frozen. The hindsight comparator can use the observed response matrix when planning, and the same coarse observation when acting. The replay models independent erasure at both opening sends, the question and the final response, and pays the existing communication costs on sends. A deterministic writer picks the best available supported clauses within 70 words. This makes incomplete evidence visible without passing model-written prose to the final record. [Transition and scoring code](replay_delivery.py)

The implementation checks the six-field replay against the original full-card net scores when all fields arrive. A separate enumerated path calculation checks the probability-weighted nets under each test admission matrix. The selection audit checks actual input and output tokens and adds nine software probes for invalid syntax, wrong IDs, field swaps, truncation and withheld content.

## A format failure hid twelve correct selections

All fifteen first-pass generations finish and return bare IDs. The requested numbered decoder accepts zero fields. All twelve ordinary sequences nevertheless contain the two correct IDs in order, with identical answers across all four question conditions for each desk. A post hoc grammar that accepts exactly two bare ID lines recovers all 24 ordinary fields while retaining the same source and field checks. The counterfactual changes admission logic only. It keeps the original invalid-format score visible. [Original responses](evidence/final-records.json) · [Numbered admission](numbered-admission.json) · [Bare admission](bare-admission.json)

| Uniform-inventory policy | Numbered decoder net | Bare decoder net | Bare requests per episode |
| --- | ---: | ---: | ---: |
| Learned budget fit | 41.425 | 52.990 | 1.000 |
| Same learned responder under silence | 41.475 | 52.929 | 0 |
| Declared excerpt planner | 41.430 | 53.095 | 0.603 |
| Hindsight joint planner | 41.650 | 53.095 | 0.603 |

Nets include the 42 public points and communication costs. With the bare decoder, the observed ordinary admission matrix equals the full-delivery counterfactual. The learned query gains 0.061 points over silence for uniform inventories and loses 0.022 for correlated duplicates. The excerpt planner gains 0.166 and 0.167, respectively. The questions influence which desk the responder selects. Within any one desk, the observed question does not change the selected fields. [Strict integrated replay](numbered-replay.json) · [Bare integrated replay](bare-replay.json)

## Recover evidence after an allowed field moves into the wrong slot

In the initial withholding controls, France substitutes a public distractor for a withheld clause, Russia correctly leaves the second field empty, and the Dominican Republic puts its surviving second-field passage in the first slot. A dependent fresh prompt with examples of both empty positions yields the same three answers. The bare positional decoder admits two of the three remaining fields, with zero absent fields forwarded. The identity decoder recovers the valid Dominican Republic passage by matching its unique ID and reassigning its registered field. It admits all three offered fields and forwards zero withdrawn fields. The wrong-slot answer and the incorrect French non-abstention remain model errors. [Withholding replay](slot-repair/results.json) · [Identity gate and software controls](identity-admission.json)

The constructed withholding stress substitutes each measured withheld response into the matching-question cell for that desk. It leaves all other cells and all learned policies fixed. Substituting the Dominican Republic row reduces learned net by 0.284 points under uniform inventories and 0.853 under correlated inventories with the positional gate. Identity recovery cuts the losses to 0.079 and 0.412. In the selected no-erasure opportunity world, the positional gate leaves the learned and silent records tied at 14/28. The identity gate restores the learned record to 16/28, tying the fixed missing-source route. Those two literal records fit within the same 70-word limit. [Withholding stress replay and rendered records](stress-results.json)

When all three matching responses are replaced, the identity gate limits learned losses to 0.122 and 0.425 points respectively, relative to ordinary delivery. The learned policy keeps its unconditional querying behavior. These stress numbers describe prescribed missing information with real model responses, not an estimated field failure rate. The two normal inventories, exact assembly, typed paraphrase catalog and same-assistant weights bound the interpretation. Eighteen generations use a frozen language model and no policy updates. The registry verifies transfer of reviewed source clauses and leaves open-world semantic detection and retention in free prose separate.

## Reproduce

Use the project Qwen environment from this directory.

```bash
export PYTHONPATH="$(git rev-parse --show-toplevel)/src" OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
for mode in numbered bare identity; do
  python admission.py "$mode" | cmp "$mode-admission.json"
done
python slot-repair/score_slots.py | cmp slot-repair/results.json
python replay_delivery.py numbered-admission.json | cmp numbered-replay.json
python replay_delivery.py bare-admission.json | cmp bare-replay.json
python stress_replay.py | cmp stress-results.json
```

Each admission audit checks exact prompt bytes and tokens, generation hashes, source-field identity, and software controls. The policy replay verifies the full-card limit against the existing planner and uses an independent enumeration of modeled transport paths to verify the learned team's net.
