# Country persona data and post-training

A data-first research repository for **dated institutional country representatives**. The initial China/Germany pilot is preserved, with a separate France/UK/India/Brazil extension. The repository contains the supplied playbook, acquired corpora, source-specific parsing, country/task categorization, event-group splits, provenance checks and a modest multi-GPU LoRA workflow.

**Explore the collection:** [interactive browser](https://huggingface.co/spaces/memo-ozdincer/country-persona-explorer) · [full research view](https://huggingface.co/spaces/memo-ozdincer/country-persona-research) · [public GitHub catalog](https://github.com/memo-ozdincer/country-persona-data) · [Hugging Face tables](https://huggingface.co/datasets/memo-ozdincer/country-persona-data). [Exploration guide and update workflow](docs/DATA_EXPLORER.md).

Start with **[the measured data report](reports/DATA_REPORT.md)**. The project contains real downloaded data, not just a source registry. Large third-party data are local under `data/` and Git-ignored; their exact download URLs and hashes are tracked in [the source lock](data/sources.lock.json).

**14 September: [France, UK, India and Brazil data release](docs/COUNTRY_EXTENSION_20260914.md)** and [12 actual policy applications](docs/COUNTRY_EXTENSION_EXAMPLES.md). The extension adds strategies, climate commitments and other official evidence in eight languages, country-context statistics and newly prepared historical decisions. The earlier [six-country knowledge preview](docs/COUNTRY_KNOWLEDGE_PREVIEW.md) shows the design change. Document volume alone is not evidence of useful persona supervision; these new releases remain review candidates.

**Post-training handoff (12 September):** [four-H100 plan, costs and milestones](docs/POSTTRAINING_PLAN.md), [exact cluster commands](docs/CLUSTER_RUNBOOK.md), and [decision-by-decision evidence](docs/DECISION_REGISTER.md). A model-tokenized 500-example pilot, 832-example balanced comparator, frozen evaluation prompts and CPU-tested LoRA plumbing are prepared. Budget approximately 1–3 four-H100 node-hours for the first before/after proof of concept, then inspect before expanding.

| Read | Purpose |
|---|---|
| [Data report](reports/DATA_REPORT.md) | Actual acquisition counts, prepared pools, quality findings and baseline results |
| [Source registry](data/source_registry.json) | Acquired, blocked and deferred sources; rights notes and acquisition priorities |
| [Data dictionary](docs/DATA_DICTIONARY.md) | Actual formats, attribution rules, lineage and split semantics |
| [Research strategy](docs/RESEARCH_STRATEGY.md) | Paper-supported choices and the experiments that decide what to do next |
| [Training workflows](docs/TRAINING_WORKFLOWS.md) | Admission, tokenizer preflight, multi-GPU LoRA, and optional preference/domain-training plans |
| [Original playbook](country_persona_playbook/README.md) | Supplied research kit, preserved unchanged |

## Use the data now

- `data/raw/`: complete downloaded OHCHR/UHRI, UNGA-DM and Speaking Volumes bulk files, plus official archive snapshots and the pinned UNBench sample.
- `data/canonical/`: parsed source-specific JSONL. The whole Speaking Volumes source is preserved; OHCHR and vote tables have focused China/Germany derivatives while the complete raw releases remain available.
- `data/prepared/pilot/pilot.canonical.jsonl`: the focused pool, including evidence, genuine QA, statements, action labels and historical text.
- `data/prepared/pilot/candidates/CHN/` and `.../DEU/`: SFT-format candidates partitioned by task and split, each with an aligned provenance manifest.
- `data/prepared/long-context/`: 17,461 candidates with larger selection budgets, retaining all parsed German Foreign Office QA histories. This is an alternative view, not extra independent data.
- `data/prepared/pilot/review/admission.csv`: explicit review decisions before a training run. Candidate does not mean universally rights-cleared or expert-approved.

Code, manifests and reports are tracked in the private GitHub repository; raw/prepared data are private and transferred separately to Trillium. An earlier Qwen3 LoRA pilot ran; see the measured results and limitations in [the regression research](docs/REGRESSION_RESEARCH.md). No multi-agent simulator is included. The dataset and preparation pipeline are the main deliverables.

## Reproduce the preparation

From this repository directory, with Python 3.11 and uv:

```bash
uv sync --locked --extra data --extra dev
uv run pytest -q
uv run persona normalize
uv run persona build --output data/prepared/pilot-rebuild
uv run persona audit data/prepared/pilot/pilot.canonical.jsonl \
  --verify-raw --output reports/pilot_audit.json
uv run python scripts/check_source_spans.py
uv run python scripts/decision_baselines.py
uv run python scripts/make_data_report.py
```

The supplied `pilot` snapshot already exists. Builds require a fresh output directory so that previous exports and review decisions cannot be overwritten or mixed with stale files. The commands above audit the delivered pilot; point subsequent audit commands at `pilot-rebuild` to inspect the rebuilt copy.

On a new checkout, reacquire the pinned source files first:

```bash
uv run persona fetch --lock data/sources.lock.json
uv run persona normalize
```

`normalize` restores tracked collection manifests and extracts the known RData archive members, checking their recorded hashes. Dynamic publisher URLs can change; a different hash fails rather than silently replacing the snapshot. A URL lock cannot guarantee a publisher will keep old bytes online. Preserve a private backup of `data/raw/` for exact long-term reproducibility. The lock and manifests contain acquisition metadata, not a redistribution license.

Fresh archive collectors live in `scripts/collect_*.py`. They retain download receipts, bounded collection limits and explicit failures. The current snapshot's discovered archive pages are recorded in the manifests. The original source registry's inaccessible sources remain listed, with their actual failure modes and next acquisition steps.

## Multilingual data expansion

The [13 September data expansion](docs/DATA_EXPANSION_20260913.md) adds 2,389 parsed source documents, 12,930 literal QA candidates and 7,578 evidence passages across eleven languages, plus a separate six-language UN evaluation corpus. These remain review candidates; the original training exports are unchanged. See the report for source scope, actual counts, review milestones and frozen-manifest reproduction.

## Experimental starting point

Compare the same instruction model with a role prompt, then with dated evidence, then with shared country/institution-conditioned SFT. Prioritize substantive policy application and supported decisions; genuine QA is useful when it contains relevant country information, and authenticity alone does not make it good supervision. Keep statement reconstruction, UPR actions and historical domain text separate. Use preferences only for diagnosed source-supported errors; consider continued pretraining only after an equal-compute ablation. Multi-agent decision-making remains a later project.

## Dated evidence retrieval

```bash
uv run persona index --input data/prepared/pilot/pilot.canonical.jsonl \
  --output data/index/pilot-20260909.sqlite
uv run persona retrieve --index data/index/pilot-20260909.sqlite \
  --query 'nuclear disarmament' --before 2026-07-01 \
  --exclude-group ACTUAL_TARGET_SPLIT_GROUP --country DEU
```

Supply the actual target's `split_group` from the manifest. Retrieval excludes unknown dates, same-day material, the target event group and quarantined documents. It cannot independently certify that a historical web page was unmodified at the time; forecasting requires additional source-time review.
