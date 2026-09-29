# Reddit country-context collection

This collection adds a separate community-discourse layer for China, Germany, France, the United Kingdom, India and Brazil. It does not extend official government persona labels to Reddit authors. Country context is based on an explicit community mapping; author nationality, residence, ethnicity and political affiliation are neither inferred nor assigned.

Prepared files live in `data/prepared/reddit-country-20260923/`. The measured counts, dates, exclusions, source checksums and community inventory are in `coverage.json` and `reports/reddit-country-coverage.json`. The [hosted coverage explorer](https://memo-ozdincer-country-persona-explorer.static.hf.space/reddit-country-20260923/index.html) presents the public summary; [prepared country files](https://huggingface.co/datasets/memo-ozdincer/country-persona-research-files/tree/main/reddit-country-20260923) follow the existing account-only research-data arrangement.

## Measured release

| Country context | Posts | Comments | Observed direct reply pairs |
|---|---:|---:|---:|
| China | 5,513 | 0 | 0 |
| Germany | 9,758 | 0 | 0 |
| France | 6,746 | 1,447,840 | 1,121,044 |
| United Kingdom | 224,447 | 484,607 | 401,180 |
| India | 32,095 | 0 | 0 |
| Brazil | 13,438 | 245,771 | 221,039 |

Total: **2,470,215 unique records** and **1,743,263 overlapping parent–reply views**. The parser scanned 25,717,392 raw rows/utterances across the selected files. Reply pairs and audit samples are derived views, not additional unique evidence. Compressed prepared artifacts total 1.18 GB.

The quality report records 2,149 IDs with conflicting archive versions, 431,133 retained comments whose direct parent is missing, 5,227 exact-text groups spanning more than one thread, and 2,537 excluded records in known NSFW threads. These limits remain visible; the collection is not declared training-ready.

## Acquired sources

| Dataset | Selected material | Important limits |
|---|---|---|
| [fddemarco/pushshift-reddit](https://huggingface.co/datasets/fddemarco/pushshift-reddit) | Every listed Parquet shard for January 2014, July 2016 and January 2018; exact community filter | Three complete archive-file month slices, not continuous coverage. Post records only. Publisher schema lacks NSFW labels and comment trees. The corpus card's overall size is not treated as measured coverage. |
| [FrancophonIA/LELU](https://huggingface.co/datasets/FrancophonIA/LELU) | Full published conversation XML, filtered by subreddit IDs matched against archive metadata | France-related communities only. Unmapped community IDs are excluded. Sequential publisher conversations are not assumed to be complete original threads. |
| [itsalissonsilva/brazil-reddit-data](https://huggingface.co/datasets/itsalissonsilva/brazil-reddit-data) | Both complete CSV files for r/brasil posts and comments | Publisher uses UUIDs in place of original Reddit IDs. These support internal joins but cannot reconstruct original Reddit permalinks. |
| [alujjdnd/Reddit-US-UK](https://huggingface.co/datasets/alujjdnd/Reddit-US-UK) | Complete Birmingham post/comment dumps and CasualUK post dump | UK local/everyday-discussion expansion, not coverage of every UK community. A repository MIT label is not proof of rights in every user-authored contribution. |

All 14 files are pinned to exact repository revisions and downloaded receipts. The acquisition totals about 4.67 GB. The broad post archive supplies actual community-specific material for all six countries. The additional conversation corpora are unevenly distributed: France, the UK and Brazil have comments, whereas the selected China, Germany and India material consists of posts. That gap is explicit; no synthetic national replies are added.

`data/reddit_source_registry.json` also records eleven alternatives and their disposition. These include GeRedE’s registered-academic-access corpus, manually gated country datasets, Arctic Shift’s inaccessible API and larger bulk archives, a misleading China-keyword dataset, and repositories containing only download links or subreddit-name lists. Catalogued sources are not counted as downloaded records. No access gate was bypassed.

## Files and meanings

Each country directory contains:

- `community-records.jsonl.gz`: unique observed post/comment IDs, prepared text, community context, date, parent/thread identifiers and source provenance. It is an evidence/research corpus, not an approved SFT dataset.
- `reply-pairs.review.jsonl.gz`: observed direct parent and reply, joined on IDs within the same thread and community. These are structural review candidates; no preferred response, factual correctness or suitability label is inferred from scores.
- `audit-sample.jsonl.gz`: up to ten content-independent ID-hash selections per observed community. These overlap the main corpus and must not be counted as extra observations or a held-out test set.

`lineage.jsonl.gz` preserves accepted source occurrences, including duplicate IDs, with their source file, checksum, physical locator and prepared-text checksum. `coverage.json` reports per-file ingestion counts, source-version conflicts, missing direct parents and cross-thread exact-text duplicates. Duplicate archive IDs have one canonical record; conflicting versions are flagged, remain inspectable through lineage and the pinned sources, and are excluded from reply-pair generation.

Every record has `country_iso3=null`, `represented_entity=null`, and a separate `country_context_iso3`. A German-speaking community such as r/de is described as transnational rather than exclusively German. Regional UK communities retain their individual names. India is not matched by substring against Indiana. French-Canadian material is not assigned to France. Source languages are not inferred from country or subreddit names; the row language field remains unknown.

## Preparation and quality controls

The parser excludes deleted/removed text placeholders, explicitly deleted authors, AutoModerator, tagged NSFW posts, descendants of known NSFW roots and prepared text shorter than 40 characters. Missing NSFW metadata is flagged, not silently treated as safe. This excludes a great deal of low-information material, but does not establish that every retained contribution is useful, civil or true.

Author fields and profile/flair fields are not carried into the prepared corpus. Recognisable user-handle links, email addresses and international telephone patterns are replaced in text, with the transformations recorded. This is limited pattern redaction, not comprehensive anonymization: free-text names or other personal details can remain, and original post/comment identifiers are intentionally retained for provenance and removal handling. Prepared bodies stay out of the public explorer.

The French source contains 114 XML-illegal control bytes. A streaming filter removes only XML 1.0-disallowed low control bytes before parsing; the original 660 MB XML is preserved byte-for-byte. The file-level removal count and row-level `xml_control_byte_filter_applied` flag make this transformation explicit. Standard XML entities and structure are parsed normally. Other unexpected malformed XML still raises an error.

Reply pairs require both records to exist, the child's parent ID to match, and matching thread/community fields. A reply cannot predate a known parent timestamp. Identical parent/reply text and source-version conflicts are excluded. The remaining pairs still often lack earlier ancestors or the root post, and are explicitly marked `direct_parent_only_not_complete_conversation`.

The normalized corpus is heavily imbalanced toward communities with published conversation archives. It must not be used to compare national prevalence, national sentiment or the number of people holding a view. Scores reflect an archive snapshot and are not truth labels or reliable cross-community preference judgments.

## Post-training use

All rows remain `split=quarantine`, `training_admitted=false`. No SFT or DPO targets have been generated from these archives. Suitable next work is review of source-grounded summaries, discourse interpretation and observed conversational structure, with appropriate content and use-rights decisions. Authentic community replies are not automatically high-quality assistant answers. Do not train a model to impersonate a national population or represent Reddit opinions as official policy.

Before creating training/evaluation splits, join whole threads, crossposts, exact-text duplicates and overlapping source snapshots into leakage-control components. The current report measures cross-thread exact duplicates but does not claim to resolve all semantic duplication. No hidden evaluation set is claimed. The deterministic audit samples remain development/review material.

The [current Reddit API terms](https://redditinc.com/policies/data-api-terms) specifically address AI training permission; the [Reddit for Researchers program](https://support.reddithelp.com/hc/en-us/articles/49381918834964-Reddit-for-Researchers-Program) provides an official research-access route. This acquisition does not claim that archive access, a mirror's license tag or private storage supplies training permission, consent, current deletion compliance or program approval. Current deletion status remains unverified. Follow source removal updates before any later use; the retained source and record identifiers support tracing affected entries.

## Reproduce

Restore the environment's existing dependencies plus `zstandard==0.25.0` and `pyarrow==25.0.1` (the versions used by this preparation environment). Source revisions and all fourteen hashes are recorded in the acquisition manifest.

```bash
.venv/bin/python scripts/collect_reddit_country.py
.venv/bin/python scripts/prepare_reddit_country.py --output data/prepared/reddit-country-rebuild
.venv/bin/python scripts/validate_reddit_country.py data/prepared/reddit-country-rebuild
.venv/bin/pytest -q tests/test_reddit_country.py
```

The preparer requires a fresh output directory. It verifies raw hashes and uses streaming Parquet, CSV, Zstandard and XML parsing, with SQLite for deduplication and thread joins. Parquet row numbers, CSV record indices, JSONL line numbers and XML event/utterance positions are source locators; they are not fabricated source character offsets. UTC archive timestamps are retained separately from the September 2026 download times.

To update the hosted coverage and prepared files after validation:

```bash
.venv/bin/python scripts/build_reddit_showcase.py
.venv/bin/python scripts/publish_reddit_country.py --publish
```

Publication adds a standalone per-country coverage explorer and a separate Reddit section to the main country pages. It does not blend community counts into the existing official-source counts. Full prepared bodies and provenance go to the existing private research dataset; the public dataset and both explorer Spaces receive only aggregate coverage and source metadata. Original third-party archives remain in their pinned source repositories and the local raw snapshot; this release does not upload those 4.67 GB again.

The preparation environment can be restored with the project's catalog dependencies and the compression decoder:

```bash
uv sync --locked --extra catalog --extra dev
uv pip install --python .venv/bin/python zstandard==0.25.0
```
