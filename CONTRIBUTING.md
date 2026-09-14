# Contributing to the persona fine-tuning data explorer

Contributions can add datasets, correct attribution, improve extraction, document a training trace or build an evaluation. Cluster access is not required to improve the explorer or propose a source.

## Preview the public explorer

```bash
python3 -m http.server 8000 --directory explorer
```

Open `http://localhost:8000`. The country/source overview runs entirely from committed JSON and static files. The advanced catalog needs the larger staged indexes, so use its hosted version when working without the research snapshots.

## Edit descriptions or training options

- `explorer/source_profiles.json`: source names, source-ID aliases and descriptions.
- `explorer/trace_types.json`: available fields, possible input/output mappings, scoring limitations and proposed training uses. These are hypotheses and schemas, not automatic admission decisions.
- `explorer/index.html`, `overview.js`, `overview.css`: the interface.
- `explorer/sources.json`: generated country/source counts, measured character lengths and real record references. Do not hand-edit counts to claim newly acquired data.
- `explorer/overview.json`: public projection of existing curated examples; source passages are explicitly redacted.

Validate without installing training dependencies:

```bash
python3 scripts/validate_source_inventory.py
node tests/explorer_overview_ui.cjs
```

## Propose or acquire a source

Open a dataset-source issue with the publisher URL, countries, languages, date coverage, access conditions, exact available fields and intended use. Distinguish a dataset you found from a dataset whose bytes and schema have been inspected. A blocked download can be tracked without implying acquisition.

For a data PR, preserve the publisher’s attribution, retrieval receipt, raw hash, parser version, stable IDs and original field values. Document speaker versus subject-country roles. Group translations and derived records with their parent events; do not declare new hidden evaluation cases for events already exposed during development. Never commit credentials or restricted raw text.

A maintainer with source snapshots can rebuild the inventory:

```bash
python3 scripts/build_source_inventory.py
python3 scripts/build_explorer_overview.py
```

The builders verify catalog pointers against original object hashes, collapse stable IDs for the country badges, and generate the public/private formats separately. Files are staged locally; publishing is a separate owner-authenticated step.

## Add a trace or environment

Specify:

1. What is supplied at inference: country, institutional role, date, question, proposal, evidence or preceding turns.
2. What the model generates: answer, recommendation, vote label, action or continuation.
3. What supplies training supervision or reward, and what the scoring does **not** establish.
4. Whether complete records, paired targets, preference pairs, a verifier or an interactive transition function actually exist.
5. Known missing context, leakage hazards, measured lengths and tokenizer settings if token lengths were measured.

Keep proposed SFT/RLVR/RL environments labeled as proposals until implemented and validated. An observed vote is not a verified explanation of its motive. A source passage is not automatically a task. A reviewer must distinguish government statements from monitoring-body evidence and joint institutional positions.

Correctness reports should link a record ID, source and exact mistaken field. Include the proposed correction and supporting evidence; do not overwrite the original observation without preserving provenance.
