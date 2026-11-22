# Test transfer on Resolution 2504 under stronger local authoring

Resolution 2504 matches both UNBench and UNSC-Bench. Freeze the two routing policies trained before its reply data were collected. On this held docket, Qwen3.5-4B writes all 12 combinations of one authorized source and either a targeted question or a preloaded local instruction. The silence arm receives a substantive generic writing prompt. The source-local system and token limits match the earlier experiment. The final record uses an authored score bank and modeled custody, loss and assembly. The docket was previously used for judge calibration. [Verified UNBench and UNSC-Bench join](../facilitator-resolution-2504-evidence/provenance.json) · [Prospective protocol](protocol.md) · [Raw replies](transcript.jsonl)

| Observed question context | Procedure | Belgium | Russia |
| --- | ---: | ---: | ---: |
| Preloaded generic instruction | 0 | 1 | 0 |
| Procedure | 1 | 0 | 0 |
| Belgium | 1 | 0 | 0 |
| Russia | 0 | 0 | 0 |

Three of twelve pass under the locked whole-card scoring item by item. All calls finish, one exceeds the 52-word budget and two introduce material source errors. The generic Belgium reply retains the exceptional nature of the mechanism. The matched Belgium reply leaves out that qualification while preserving the request for a review of alternatives. The Russia replies all correctly state withdrawal after adoption. They omit Russia's stated causal link to that adoption, which the strict reply gate covers in “in light of”. A separate chronology replay credits the correct sequence, consistent with the higher-level final-record rubric. It admits three Russia replies within budget and preserves all raw wording. The calls use 2,128 input and 760 generated tokens. [Exact spans and whole-card matrix](admission.json) · [Chronology-only sensitivity](chronology.json)

## Transfer and label controls

The table gives net gain over the best no-request responder with knowledge of the held admission matrix on the same opening and transport. Policies that use ideal admission for inference receive the public eligibility scores and the assumed ideal channel. They receive no held admission marks at decision time.

| Setup | Uniform | Correlated |
| --- | ---: | ---: |
| Ideal-trained policy, strict whole-card admission | −3.351 | +3.599 |
| Exact planning under assumed ideal admission, strict whole-card admission | −0.590 | +0.761 |
| Ideal-trained policy, chronology sensitivity | −1.977 | +3.138 |
| Exact planning under assumed ideal admission, chronology sensitivity | +0.140 | +0.297 |
| Hindsight joint planning, strict whole-card admission | +0.066 | +3.782 |
| Hindsight joint planning, chronology sensitivity | +0.892 | +3.589 |

The ideal-trained policy keeps these net values under all six card renumberings. Each relabeling preserves semantic opening policies and inventory probabilities, and the code independently rebuilds each opening law. The measured-admission fit asks zero questions and trails hindsight no-request under both priors on the original labeling. The ideal-trained policy asks on every opening with positive probability. [Frozen replays and all label permutations](replay.json)

With uniform inventories, the opening includes both Procedure and Russia with probability 0.215. The ideal-trained chair then asks about Belgium, but the topical Belgium answer loses a qualifier that the preloaded generic answer preserves. That branch accounts for −2.658 of the strict net gap. Under correlated inventories, the opening includes Belgium and Russia with probability 0.225. A procedure question recovers the missing third source in enough branches to contribute +2.721 net. The sign change follows the inventory-dependent value of requesting a complement and the content of the reply. [Per-opening contributions](origins.json)

The separate fact-level replay gives an incomplete but factual reply credit only when its supported facts complete an authored criterion. It changes the strict ideal-trained gain to −3.122 and +3.544. Under chronology-based scoring, the original-label policy results are unchanged by this additional credit. Admitted fraction, drafted-record quality and routing utility still measure different stages. The transfer result concerns one new reply matrix with a previously examined docket, fixed local prompts, exact-span same-assistant reviews and modeled transport. [Fact-credit graph and scores](atom-protocol.md) · [Fact-level replay](atoms.json)

## Reproduce from the parent directory

```sh
export PYTHONPATH="$(git rev-parse --show-toplevel)/src"
export OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
python facilitator_2504_routing.py blind facilitator-2504-routing-evidence
python facilitator_2504_routing.py score facilitator-2504-routing-evidence
python facilitator_2504_routing_replay.py
python facilitator_2504_routing_atoms.py
python facilitator_2504_routing_chronology.py
python facilitator_2504_routing_origins.py
```
