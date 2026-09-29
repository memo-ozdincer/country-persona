# Four-country policy workshop: post-training formats

This release develops ten source-backed France, UK, India and Brazil policy cases into **53 candidate export rows in four formats**, plus three readable collaborative episodes. These are correlated views of ten cases from eight documents, not 53 independent observations. It uses the existing official-source collection; no extra web data or model-generated documents were needed.

Open [the local visual review](../data/prepared/policy-workshop-20260916/showcase.html). It shows complete collaborative handoffs, chosen/rejected comparisons and expandable exact source excerpts. The report is self-contained and works from disk. The [public showcase](https://memo-ozdincer-country-persona-explorer.static.hf.space/policy-workshop-20260916/showcase.html) is hosted on Hugging Face; [complete training files](https://huggingface.co/datasets/memo-ozdincer/country-persona-research-files/tree/main/policy-workshop-20260916) are in the existing private research dataset. No training job was submitted.

## What is included

| Export in `data/prepared/policy-workshop-20260916/` | Rows | Supervision |
|---|---:|---|
| `audit.sft.jsonl` | 20 | JSON claim audits: ten correct drafts accepted unchanged and ten flawed drafts corrected; structured facts, nulls for unestablished facts, citations and evidence limits |
| `revision.sft.jsonl` | 10 | Minimal source-grounded correction of a flawed briefing sentence |
| `preference.dpo.jsonl` | 10 pairs | Same prompt and comparable answers; chosen is grounded, rejected contains one controlled semantic error |
| `multiagent.sft.jsonl` | 13 | Separate analyst, verifier and editor prompt/completion rows across three workflows |
| `episodes.jsonl` | 3 | Workflow graph, participant identity, dependencies, visible evidence, all public work products and rubrics |
| `evidence.jsonl` | 10 | Exact source excerpts, offsets, pages, original/extracted SHA256 receipts, publisher URLs, attribution and date caveats |
| `review.csv` | 13 units | Blank review ledger covering ten cases and three workflows |

Each training-format file has an aligned `.manifest.jsonl`: stable IDs, row hashes, provenance links, synthetic derivation, language, countries, source groups and connected split component. Each source excerpt is embedded in the model prompt, so inference does not depend on implicit retrieval.

The supported-error types are alliance relationship, unsupported doctrinal precision, priority reversal, sector exclusions, intensity versus absolute emissions, voluntary versus mandatory waiver, livelihood qualifications, baseline year, the scope of other members’ flexibility and attribution of a sanctions position. The Portuguese Brazilian sources retain their exact Portuguese excerpts; English annotations are authored paraphrases, not official translations.

## The collaborative cases

**Climate comparison:** UK, Indian and Brazilian analysts preserve the distinct metrics, baselines, dates and exclusions. A verifier audits a deliberately flawed comparison; the editor explains why the percentages cannot establish a common ranking. Five supervised turns.

**WTO development flexibility:** Indian and Brazilian analysts distinguish a national waiver from support for other members’ flexibility. The verifier corrects an invented disagreement; the editor identifies limited textual compatibility without claiming a joint agreement. Four supervised turns. The reports have different dates: this is expressly not a simultaneous historical negotiation.

**European and Atlantic defence:** French and UK analysts identify the actual priorities in their strategy excerpts. The verifier rejects an invented French departure from the Atlantic framework and a fabricated UK US-only procurement rule. The editor preserves shared ground and distinct emphasis. Four supervised turns.

These are **authored collaborative research demonstrations**, not observed model rollouts, authentic intergovernmental exchanges, private reasoning traces, RL trajectories or demonstrated negotiation competence. The flawed editorial drafts are supplied synthetic task material, not sampled prior agent outputs. No runtime agents or simulator are required to consume the completion exports.

Each analyst sees only its assigned source. The verifier sees the sources, analyst notes and flawed editorial draft. The editor additionally sees the verifier’s work. Agent identity is supplied in the task prompt and metadata, while chat roles remain ordinary `system`, `user`, `assistant`. Other agents’ work is user-context data, never additional assistant targets. There are no future outputs in earlier prompts.

## How to use the files

SFT rows have conversational `prompt` and `completion` arrays. Preference rows have conversational `prompt`, `chosen` and `rejected` arrays. All carry `chat_template_kwargs: {"enable_thinking": false}`. Preserve that setting when rendering the chat template; JSONL metadata does not automatically configure every training library.

Use completion-only loss for the SFT projections. The deliberate errors belong in prompts or rejected preference completions; never concatenate the episode into a transcript and supervise every turn indiscriminately. Keep the manifest adjacent to each export, verify row hashes before selection, and carry its provenance and group IDs through any admission pipeline. These manifests are specific to this release; they are not a drop-in replacement for the older authentic-QA training manifest.

For a first format experiment, use one primary SFT view, then compare against the collaborative view under equal evidence exposure. The revision and audit rows already teach the preferred corrections used by the preference pairs, so adding all formats without accounting for duplication would mainly repeat the same answers. Treat DPO as a separate format candidate; these ten controlled pairs have not demonstrated an improvement over SFT and are not mined model failures. Limit sampling per underlying case/component rather than counting rows as independent evidence.

All rows retain `split=quarantine`, `training_admitted=false`, and `fresh_evaluation_eligible=false`. This preserves the existing project admission convention; it does not require more formatting work to inspect the candidates. Source rights and independent semantic review remain unresolved. The blank review ledger intentionally does not fabricate reviewer approval.

## Splits and temporal scope

Cases sharing a source group stay together. Team comparisons merge their source groups transitively, yielding only **four connected leakage components**: climate, WTO, defence, and the standalone Brazilian sanctions passage. All alternate formats inherit those components. Do not randomly split rows or hold out a team synthesis while training on its analysts’ same source facts.

The release adds no clean test set. These same policy sources and claims already appear in the prior country-extension material; any later split must also respect those upstream copies and translations. The manifest preserves upstream proposed splits without converting them into admission. It records unknown historical availability explicitly, including the French translation and Brazilian compendium. Every task is retrospective document analysis, not a forecast from information supposedly available at a historical decision time.

An eventual held-out assessment needs fresh source/event components and independent annotations. Four connected components are too few to support a convincing train/dev/test performance claim.

## Reproduce and validate

From the repository root:

```bash
.venv/bin/python scripts/build_policy_workshop.py \
  --output data/prepared/policy-workshop-rebuild
.venv/bin/python scripts/validate_policy_workshop.py \
  data/prepared/policy-workshop-rebuild
.venv/bin/python scripts/preflight_policy_workshop.py \
  data/prepared/policy-workshop-rebuild \
  --report reports/policy-workshop-rebuild-preflight.json
.venv/bin/pytest -q tests/test_policy_workshop.py
```

The builder requires a new output directory, verifies both original-source and extracted-text receipts, binds exact offsets, and preserves upstream country attribution. Repeated builds from identical inputs are byte-reproducible. The independent validator checks receipts, row alignment, references, workflow dependencies, source visibility, positive controls and component consistency. Tests exercise source corruption, invalid offsets/pages, country exclusion, transitive leakage groups, shuffled export rows and reproducibility.

The offline preflight uses the repository’s locked Qwen3-8B tokenizer, tests both preferred and rejected completions, checks the exact prompt/completion boundary and refuses to truncate. See [the measured tokenizer report](../reports/policy-workshop-preflight.json). Tokenization checks establish format/length suitability, not model quality or trainer integration.

Authored definitions are tracked in `data/curation/policy_workshop_cases.json` and `data/curation/policy_workshop_teams.json`; the prepared files and source text follow the repository’s existing ignored-data layout. Germany/China decision preparation and the shared explorer were not edited by this work.
