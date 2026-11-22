# Verify source fragments before assigning a documentary reward

Replace the role's paraphrasing step with passage ID selection. The input contains the authorized excerpts, plain-language fields, one public distractor and the received question. The host only publishes fragments whose IDs match its pre-authored source map. The same map links the field to an independent or joint criterion. The evaluator saves actual selected text with the model call and assembly source. A complete authored catalog is a prerequisite. [Protocol](protocol.md) · [Catalog fragments and field descriptions](fields.json)

Across Resolutions 2719 and 2504, run all 24 source and message pairs plus six controls with a required passage withheld. The 30 responses use 9,973 input and 424 generated tokens. All parse. The ordered reply contract admits 15/24 complete cards. Decoding by passage identity on the same outputs admits 19/24. It recovers passages the model selected on the wrong numbered line. The gate emits the other two validated fields in all six withheld controls and never emits the withheld field. The model explicitly writes EMPTY on the correct line in only one of six controls. The host's ability to withhold unsupported fields and the model's ability to express uncertainty are separate results. [Raw ordered admissions](admission.json) · [Identity-based selection and verified assembly](identity.json)

On Resolution 2719, decoding by identity admits all 12 full-card replies. All question contexts, including preloaded generic writing, have the same evidence availability. The remaining advantage therefore comes from a different source being routed, with terminal output held to the same documentary standard. On Resolution 2504, the procedural tally is never selected in its original fragment form. All four procedural replies omit it, and one off-topic call also omits the penholders' adoption request. Partial field credit on these matrices preserves verified evidence but does not add net reward, because the fragments that survive do not complete an additional criterion. [Scorer and authored dependency audit](atom-protocol.md) · [Field-credit diagnostics](atoms.json)

| Ideal-trained policy vs hindsight no-request | Uniform net gain | Correlated net gain |
| --- | ---: | ---: |
| Resolution 2719, identity decoding | +0.696 | +0.242 |
| Resolution 2504, identity decoding | +0.807 | −0.511 |
| Resolution 2719, exact joint planning | +0.786 | +0.505 |
| Resolution 2504, exact joint planning | +1.105 | +0.230 |

The first pair uses measured certificate outcomes and frozen prior weights. Exact joint planning also knows the measured channel. A perfect-certificate reference is reported separately. The test uses a curated source map, exposed UN cases and simulated transport. It evaluates documentary routing after source registration and leaves open-ended factual judgment and general deliberation evaluation distinct. [Whole-card replay, costs and no-question-writer ablation](replay.json) · [Resolved and unresolved passage IDs](identity.json)

## Reproduce from the parent directory

```sh
export PYTHONPATH="$(git rev-parse --show-toplevel)/src"
export OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
python facilitator_passage_routing.py score facilitator-passage-routing-evidence
python facilitator_passage_routing_replay.py
python facilitator_passage_routing_atoms.py
python facilitator_passage_routing_identity.py
```
