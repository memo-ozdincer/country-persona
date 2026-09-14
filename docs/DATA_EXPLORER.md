# Explore the country-persona data

**Presentation update:** Start with the [country overview](https://memo-ozdincer-country-persona-explorer.static.hf.space/index.html). It shows characteristic policy applications, distinct record-ID counts by type, and colour-coded training fields. See [format and count definitions](EXPLORER_PRESENTATION.md). The filter-heavy catalog remains at `advanced.html`; the two-event Ukraine comparison is explicitly a limited subset. The object totals below describe the underlying catalog, not independent training traces.

Project owner and publisher: **Memo Ozdincer** (`memo-ozdincer`).

- [Public interactive explorer](https://huggingface.co/spaces/memo-ozdincer/country-persona-explorer): a country overview with characteristic examples, counts by type and annotated training formats. The full catalog retains search, filters and file inventory.
- [Full research explorer](https://huggingface.co/spaces/memo-ozdincer/country-persona-research): sign in as the owner to read original records and download the complete research files.
- [Original research archive](https://huggingface.co/datasets/memo-ozdincer/country-persona-research-files): owner-only download of all original files, with a per-file integrity inventory. It is stored separately to keep the static Space below the service’s 1 GB limit.
- [Public Hugging Face tables](https://huggingface.co/datasets/memo-ozdincer/country-persona-data): separate subsets for each record type, including decisions, policies, statistics, evidence, training/evaluation views and file metadata.
- [Public GitHub catalog](https://github.com/memo-ozdincer/country-persona-data): country pages, worked examples, source attribution, data dictionary and reproducible explorer code.

## How to explore

Start with the **country overview**. Choose a country, read its characteristic policy application and inspect the prompt, evidence, target answer and review metadata. The examples are authored review candidates. Expand the JSON preview to see the actual fields; public source passages are explicitly omitted. Source links retain publisher attribution.

The secondary **Full catalog → Compare decisions** page covers only two Ukraine resolutions. Each event has six country views, final votes, located statements and explicit missing context. It is not the coverage of the whole corpus.

In **Full catalog → Explore records**, start with policy positions, policy applications or country statistics. Use the country buttons and filters together. Search covers metadata, titles and public summaries. Select a record to see its readable fields, original publisher links, evidence pages, readiness and full structured representation. Download matching metadata exports all matching index records, not just the displayed page. The Hugging Face tables retain the full public provenance fields. Filters and selected record are encoded in the URL for sharing. Date filters include records whose known year or month overlaps the requested interval; this does not upgrade their date precision or prove contemporaneous availability.

**All source files** inventories every file beneath raw, canonical and prepared data, including receipts and alternative training views. A file inventory entry is not a claim of unique substantive content. The full research view adds original JSON and source text on demand, plus a complete archive download of all research files. Public presentation keeps source attribution and links without redistributing third-party full text under an invented blanket license.

## What the counts mean

The current build indexes every nonblank row in all 238 canonical/prepared JSONL files, and inventories all 11,901 raw/canonical/prepared files. It reduces 528,093 row occurrences to 303,951 exact distinct JSON objects, retaining every source path, line and byte offset. This is exact object deduplication, **not** deduplication of events or semantically equivalent examples. Review manifests, translations, derived passages and alternate training formats are explicitly included and overlap. See `reports/data-catalog.json` for the generated breakdown.

An identical object can occur in multiple collections. Collection filters match all recorded locations, not merely the first one. Multi-topic records can be found under each individual topic. Missing training admission is `not_recorded`, not approval. Existing train/dev/test fields remain visible; the Hub's `catalog` split is only a browsing container.

All raw files are inventoried, but large raw CSV/JSON archives are not each converted row-for-row into this catalog. Their canonical/prepared derivatives are indexed; the complete archives remain downloadable in the full research view. This distinction matters for global corpora whose focused country derivatives are smaller than the upstream archive.

## The new decision representation

The release adds 12 retrospective decision cases across six countries and two events: the final votes on A/RES/ES-11/1 and A/RES/ES-11/4. Seven cases include an attributed statement: five explanations of vote and two pre-vote statements. These categories are kept distinct. The other five cases have proposal and vote evidence, with explanations marked missing.

Each case preserves:

- Actual draft symbol and evidence, adopted resolution symbol and event date.
- Original final vote, amended label, primary meeting-record reference and bulk-data line.
- Attributed statement or explanation, exact source span and evidence pages.
- Stated considerations and requested changes, distinct from demonstrated conditions for agreement.
- Missing material context, unknown private motives and review status.

For October 2022, joining only on resolution number would also retrieve three procedural decisions. The builder explicitly selects `A/RES/ES-11/4-FP`, the final decision. Brazil's explanation states that its proposed call to cease hostilities and negotiate was omitted, yet Brazil voted in favor. The case therefore records a requested change without inventing a necessary condition for support. The relevant [primary meeting record](https://docs.un.org/A/ES-11/PV.14) was checked against PDF p. 17.

These cases are not a hidden benchmark. They reuse historical events already present in the archive, include post-vote explanations, and have been exposed for development. All are quarantined and unadmitted. No new GPU job was launched.

## Update workflow

Run from the original research repository after restoring the frozen source data:

```bash
.venv/bin/python scripts/build_decision_cases.py
.venv/bin/python scripts/build_data_catalog.py
.venv/bin/python scripts/stage_data_publication.py
.venv/bin/python scripts/stage_static_explorer.py
.venv/bin/python -m pytest -q
# Uses the owner's existing Hugging Face login; never embed a token.
.venv/bin/python scripts/publish_data_catalog.py
```

The catalog discovers new canonical/prepared JSONL files automatically. Add newly sourced decisions as the same structured case type to make them appear in comparison and browsing views. Preserve unknowns instead of filling them with model guesses. For a new decision, acquire the exact proposal, distinguish final from procedural votes, locate an attributed explanation, inspect qualifiers and source dates, and preserve the event's existing split relationships. Public summaries must remain source-grounded and separate from original transcripts.

Local full-data view:

```bash
CATALOG_DB="$PWD/.cache/data-publication/catalog.sqlite" \
CATALOG_STATS="$PWD/.cache/data-publication/stats.json" \
PRIVATE_DATA_ROOT="$PWD" \
.venv/bin/python explorer/app.py
```

Open http://127.0.0.1:7860. The local server binds to loopback by default. Full records are read only from indexed paths and checked against their content hash before display. Public deployments contain no source archive; the separate account-only static deployment contains the original record chunks and research archive behind Hugging Face's access controls.

## Format and research basis

The public Hub release uses [explicit Parquet subsets](https://huggingface.co/docs/hub/datasets-data-files-configuration), small row groups and page indexes. The explorer uses [SQLite FTS5](https://www.sqlite.org/fts5.html) with parameterized filters. [Static Spaces](https://huggingface.co/docs/hub/spaces-sdks-static) host the browser without a running server. Hosting via Docker was rejected by the service as requiring PRO; no subscription was purchased. The static view loads metadata by record type and gzip-compressed detail chunks on demand. The original-file archive lives in a separate private dataset because the service rejected a Space above 1 GB. No model API or paid inference endpoint is needed.

[UN General Debate Corpus](https://arxiv.org/abs/1707.02774) motivates attributing public state positions, without claiming private preferences. [CheckList](https://aclanthology.org/2020.acl-main.442/) motivates behavioral cases that test distinctions such as requested change versus condition of support. Existing [training decisions](DECISION_REGISTER.md) and [four-country source methodology](COUNTRY_EXTENSION_20260914.md) retain their literature links. This catalog does not certify source permissions, annotation quality or persona performance.
