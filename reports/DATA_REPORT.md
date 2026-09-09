# Acquired data and prepared pilot

Snapshot: 9 September 2026. Counts below were measured from downloaded files and executed parsers; they are not the source-registry estimates.

## What is on disk

| Source | Acquired source material | Parsed output |
|---|---|---|
| mfa | 982 pages | 982 press_conference, 9,005 authentic_qa |
| germany_press | 179 pages | 179 press_conference, 1,541 authentic_qa |
| china_mission | 996 pages | 962 statement_reconstruction |
| germany_mission | 453 pages | 452 statement_reconstruction |
| ungdc | 126 pages | 126 domain_text |
| Speaking Volumes UNGA corpus | 32,366 source segments, 203 source country labels, 1992–2018 | 33,046 originals + speaker-span derivatives |
| OHCHR/UHRI | 274,991 records, including 130,991 UPR | 9,894 focus-related records/derivatives |
| UNGA-DM | 1,205,730 country-decision observations, 7,509 decisions | 16,130 China/German historical-entity vote rows |
| UNBench GitHub sample | 30 vote rows plus 34 nested statements; 41 pinned files | 64 benchmark records; the sample contains no China/Germany vote rows |

Counts include different units and derivatives. Do not add the table rows and describe the total as independent training examples. Complete OHCHR, UNGA-DM and Speaking Volumes source releases are retained locally; the official archives are snapshots of their discovered indexes, not a claim to cover every statement ever published.

## Prepared country/task pools

A second, longer-context export is available at `data/prepared/long-context/`: **17,461 candidates**, retaining all 1,541 parsed German Foreign Office answers with their full prior histories. These are alternative views of the same records, not additional independent data. Tokenizer checks remain necessary.

The focused canonical pool contains **37,094 records**. There are **16,373 SFT-format candidates** after the implemented selection rules. These are candidates, not an expert-adjudicated or universally rights-cleared training release.

| Country | Task | Train | Dev | Test |
|---|---|---:|---:|---:|
| CHN | authentic_qa | 7,607 | 982 | 294 |
| CHN | statement_reconstruction | 1,161 | 118 | 50 |
| CHN | upr_recommendation | 335 | 441 | 395 |
| CHN | upr_response | 336 | 329 | 423 |
| DEU | authentic_qa | 299 | 198 | 38 |
| DEU | statement_reconstruction | 515 | 45 | 10 |
| DEU | upr_recommendation | 804 | 674 | 495 |
| DEU | upr_response | 225 | 254 | 345 |

Calendar policy: train through 2025, dev January–June 2026, test July–September 2026. UPR cycles 1–2 train, cycle 3 dev, cycle 4 test; the more restrictive group assignment wins. Benchmark groups remain test. Unknown/future dates and incompatible historical entities are quarantined. Parent records, exact long-text mirrors, symbols and supplied families are grouped before export.

Separate candidate files live under `data/prepared/pilot/candidates/CHN/` and `.../DEU/`. Full targets and histories excluded by the short-context character budget remain in canonical data. No missing examples are replaced by invented dialogue.

## Selection and quality

| Exclusion | Records |
|---|---:|
| attribution_or_parse_flag | 232 |
| duplicate | 6 |
| over_character_budget | 1,089 |
| evidence_or_domain_only | 14,496 |
| outside_focus_country_role | 4,898 |

6 duplicate candidates are marked with their retained counterpart. Audit errors: **0**. Raw files whose hashes were checked: **2,736**.

The audit covers schema validity, IDs, exact text/group leakage and byte provenance. It does not prove semantic independence, resolve recurring-resolution families, or eliminate base-model pretraining contamination.

Parsing exceptions are retained in `reports/normalization.json`. Linked ministerial pages in the Chinese mission index need separate institutional attribution; a German joint-statement page links its content rather than providing an extractable speech body. They stay raw and are not silently trained as national mission statements.

## Important findings

- Chinese MFA archive migrations separate the original conference date from a later publication date. Both are retained.
- All authentic QA targets are checked against source HTML after whitespace normalization; see `source_span_audit.json`. This checks literal grounding, not political interpretation.
- German Foreign Office targets are selected by the `(AA)` speaker label. Other ministries remain prior context.
- Mission coalition statements and historical governments are not silently turned into modern national supervision.
- Speaking Volumes contains chair text, occasional other speakers and non-ISO country codes. Originals and extracted speaker spans remain separate; available UNGA-DM meeting dates are joined with provenance.
- UPR labels include Supported/Noted. A supported recommendation is not evidence of implementation.
- UNGA-DM retains original/amended votes, absences and suspended non-voting. Missing proposal text keeps this pool out of SFT vote prediction.
- The small UNBench sample cannot supply a China/Germany voting benchmark. The full release and a proposal-text join remain acquisition priorities.

## First empirical diagnostic

| Country | Split | Rows / groups | Majority prediction | Accuracy | Balanced accuracy |
|---|---|---:|---|---:|---:|
| CHN | dev | 329 / 1 | Supported | 0.854 | 0.500 |
| CHN | test | 423 / 1 | Supported | 0.686 | 0.500 |
| DEU | dev | 254 / 1 | Supported | 0.815 | 0.500 |
| DEU | test | 345 / 1 | Supported | 0.820 | 0.500 |

These are CPU-only majority baselines learned from the train split, not LLM results. High accuracy can coexist with poor class balance. A small number of review events limits what thousands of recommendation rows can establish.

## Remaining work before model-quality claims

Source-level use decisions, expert samples of role/position fidelity, recurring-family adjudication, model-specific token preflight and the first GPU smoke run remain. The repository supplies a multi-GPU LoRA starter and a paper-based experiment plan. It does not contain a trained country model, a synthetic preference corpus or a multi-agent simulator.

See `docs/RESEARCH_STRATEGY.md`, `docs/TRAINING_WORKFLOWS.md`, `docs/DATA_DICTIONARY.md`, and `data/source_registry.json`.
