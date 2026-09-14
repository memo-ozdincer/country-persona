# Country-persona data expansion — 13 September 2026

The expansion adds **2,389 parsed official documents, 12,930 literal Q&A candidates, and 7,578 source-linked evidence passages**. Separately, the publisher's UN Parallel Corpus development/test sets provide **8,000 aligned segments across six languages**. Collection and preparation used CPU/network resources and **zero four-H100 node-hours**. No training job was submitted.

These are additions to the previous release, not a replacement. They are more authoritative and better documented than generic persona descriptions, but their usefulness for training still needs content review and a controlled experiment. No new examples have been marked expert-approved or automatically admitted to training.

## What was acquired

| Source | Parsed documents | Literal QA candidates | Language coverage | Intended use |
|---|---:|---:|---|---|
| China MFA regular briefings, Chinese | 382 | 3,243 | Chinese | Original-language responses with reporter questions and earlier dialogue |
| China MFA regular briefings, French | 381 | 3,236 | French | Publisher language versions; multilingual consistency |
| China MFA regular briefings, Spanish | 383 | 3,255 | Spanish | Publisher language versions; multilingual consistency |
| China MFA regular briefings, Russian | 377 | 3,196 | Russian | Publisher language versions; multilingual consistency |
| China UN Mission statements and reports | 400 | — | Chinese | Security Council, General Assembly and other UN policy evidence |
| German Federal Foreign Office newsroom | 436 | — | English, German | Speeches, interviews, press statements and other policy evidence |
| Latest fourth-cycle UPR national reports | 12 | — | Arabic, Chinese, English, French, Russian, Spanish | Two national submissions in six language versions, held out |
| Strategies, white paper and WTO government report | 18 | — | Eleven languages in total | Explicit policy commitments and cross-language attribution controls |

The 18 policy documents contain Germany's China Strategy in German, English and Chinese; its National Security Strategy in four full versions (German, English, French, Spanish), seven translated summaries (Arabic, Chinese, Japanese, Polish, Portuguese, Russian, Ukrainian), and German/English summaries; China's 2021 international-development-cooperation white paper in English; and China's 2024 WTO government trade-policy report in English. The strategy summaries are **not full translations**. The [German strategy publisher](https://www.nationalesicherheitsstrategie.de/en.html), [China Strategy publisher](https://www.auswaertiges-amt.de/en/aussenpolitik/regionaleschwerpunkte/asien/strategy-on-china/2608618), [Chinese government white paper](https://english.mee.gov.cn/Resources/publications/Whitep/202101/P020210122374486901993.pdf) and [WTO report](https://www.wto.org/english/tratop_e/tpr_e/g458_e.pdf) are the acquisition sources.

The UN language evaluation corpus has 4,000 development and 4,000 test segments, each aligned in all six official languages: **48,000 language-specific strings, not 48,000 independent examples**. The two publisher splits contain 732 and 731 documents respectively, with zero shared document IDs. The full UN training corpus was not downloaded. [Publisher description and paper](https://aclanthology.org/L16-1561/).

## What the counts do and do not mean

The collector downloaded 2,468 source documents/pages. Parsing retained 2,389 and excluded 79: 76 non-regular-conference archive items, two short German articles, and one French conference whose extracted QA failed the contiguous source-span check. All exclusions remain in the acquisition manifest. Two normalized duplicate documents remain traceable in the document ledger but are omitted from evidence-passages export.

There are **848 conservative document/event groups**, and 574 multilingual families within the new release. These group counts are not a claim of independent new facts: mission documents sometimes share a conservative day group, and many briefing events already exist in the English release. **1,035 new document versions belong to groups that overlap prior training events**, so those groups cannot provide fresh generalization evidence. Same-day grouping is intentionally conservative, not proof of exact translation equivalence.

Coverage is uneven. The expansion contains 1,931 Chinese-country documents and 458 German-country documents; most new authentic QA is Chinese. Eleven languages does not mean eleven equally substantial or equally matched country corpora. Japanese, Polish, Portuguese and Ukrainian coverage is currently a German strategy summary each. Do not concatenate this expansion into a training run at natural frequency.

## How the data is prepared, and why

**Preserve the actual institutional speaker.** A Chinese ministry's French text is Chinese policy evidence; a German strategy written in Chinese is German policy evidence. A UN report or joint statement has its own author/coalition. Ministry articles remain evidence documents until direct-speech attribution is checked. Country positions in public texts are evidence of expressed policy, not citizens' personality or private negotiating intent. The [UNGDC paper](https://arxiv.org/abs/1707.02774) motivates analyzing country positions from attributable diplomatic speech; it does not validate every persona simulation.

**Separate source text, response supervision and evaluation.** Complete documents, literal QA, retrieval passages, language families and review records are separate JSONL outputs. Authentic QA retains the published question, answer and preceding exchanges. No LLM-generated questions, translations or answers were substituted. Long policy documents have exact character-span passages and PDF page locators. The 3,000-character passage cap is an indexing convenience, not a token budget or literature-prescribed optimum. Tokenization and context selection still belong to the next training release.

For the next experiment, source-grounded question answering is a stronger hypothesis than teaching the model to recite whole documents. [RAFT](https://arxiv.org/abs/2403.10131) provides evidence for training with relevant and distracting retrieved documents. We adopt the evidence-grounding principle, not its exact chain-of-thought recipe; the project still uses Qwen3 with thinking disabled. Preparing a retrieval corpus alone does not reproduce RAFT or prove that hallucinations will fall.

**Group translations before splitting.** Explicit German publisher `hreflang` links define language families. China MFA versions share the conference date from the title, rather than the URL/upload date; translated pages sometimes appear later. UN national reports group by document symbol. Strategy summaries and full texts have different translation-family labels but share one split group. [Yao et al., EMNLP 2024](https://aclanthology.org/2024.emnlp-main.990/) show that translated benchmark contamination can inflate measured performance. [Artetxe et al., EMNLP 2020](https://aclanthology.org/2020.emnlp-main.618/) show that translation artifacts can affect cross-lingual evaluation. Consequently, exact text matching alone is insufficient.

**Keep existing holdouts intact.** Proposed chronological boundaries remain train through 2025, development through June 2026, test thereafter. The most restrictive known group allocation wins; later publication can move a translation's entire family later. Fourth-cycle UPR reports remain test regardless of their 2023 issue dates. The public UN dev/test corpus never enters training. All new country records currently have `split=quarantine`, `training_admitted=false`, and a separate `proposed_split`; existing admitted/tokenized exports are unchanged. This is a candidate release, not a new ready-to-launch checkpoint recipe.

**Verify mechanically, then review content.** Raw SHA256 values, normalized QA source spans, exact evidence character offsets and schema requirements were checked. Matching against the previous release includes event IDs, normalized complete text and long held-out paragraphs. This is not complete semantic or cross-language deduplication. [Lee et al., ACL 2022](https://arxiv.org/abs/2107.06499) supports deduplication as a useful data-quality intervention; it does not imply these checks catch all duplicates.

PDFs retain original bytes, page boundaries and extracted text. Representative Chinese and Arabic pages were visually inspected; all pages/languages have not been manually reviewed. In particular, Arabic bidirectional marks, PDF column order, footnotes, tables and summary omissions require review before answer supervision. China's UPR report includes a technical reissue in January 2024; issue date, review date and translation availability must not be collapsed into one date.

**Record rights per source.** The UN Parallel Corpus's included disclaimer and attribution requirements are retained with the prepared sets. Other source records retain unresolved source-use status; the [German Foreign Office notice](https://www.auswaertiges-amt.de/en/nutzungsbedingungen-neu2011-386532) explicitly reserves copyright. Public access is not recorded as a blanket training or redistribution license. Git stores provenance/manifests, scripts and reports; source text stays in the private data directories.

## The next small, informative experiments

These milestones are proposed next work, not completed evaluations. Thresholds below are project acceptance choices, not claims that a paper establishes a universal number.

| Milestone | Data and inspection | Evidence required before proceeding |
|---|---|---|
| 1. Content audit | Prepared `review-100.jsonl`: 50 records per country, all German strategy languages, and four MFA QA languages. Inspect speaker, country/coalition, exact QA boundaries, date and translation scope. | No wrong-country targets; repair systematic parser errors; proposed target ≥98% correct extraction/attribution in the reviewed packet. Reviewers and ratings are currently unset. |
| 2. Grounded evaluation set | Author and independently review 100 matched scenarios, each asked of China and Germany; include agreement cases, unsupported requests, changing policy dates, and country-name-masked answers. Link every expected claim to evidence. | A real disagreement should be supported by sources; shared positions must not be artificially separated. Reserve entire event/document families before writing training examples. |
| 3. Retrieval proof of concept | Compare the unchanged base model with country prompting versus country prompting plus these reviewed sources. Start with English, then a matched English/German/Chinese subset. | Inspect unsupported claims, wrong-country borrowing, answer relevance, citations and repetition. Look for more accurate policy differences rather than a higher country-classifier score alone. |
| 4. Small SFT ablation | Only after the above, build roughly 500 balanced reviewed examples; compare the existing authentic-QA recipe with an evidence-conditioned recipe at matched token/compute budgets. | Improvement on held-out grounded scenarios without losing shared-position agreement or language consistency. Count distinct events and supervised tokens, not just rows. |
| 5. Broader languages | Add reviewed French/Spanish/Russian scenarios with matched evidence scope. Use summary-covered claims only when evaluating summary-only languages. | Country identity should remain stable when language changes. Do not count a translated version of a trained event as unseen knowledge. |

[CheckList](https://aclanthology.org/2020.acl-main.442/) motivates behavioral tests and controlled input variations. [FActScore](https://aclanthology.org/2023.emnlp-main.741/) motivates checking individual claims against evidence. These are methodological starting points; diplomatic attribution and legitimate country agreement require task-specific review. Additional RL, preference training or continued pretraining is not justified merely by acquiring more text. Current model regressions and the earlier measured GPU pilot are discussed in [the regression research](REGRESSION_RESEARCH.md).

## Remaining acquisition priorities

1. **UN meeting records + resolutions + explanations of vote.** Join by document symbol and meeting date, then extract speaker spans and whether the representative is speaking nationally or for a group. This is the best next source for eventual decision-making tasks. The [UN Library's research guide](https://www.un.org/en/library/researching-security-council) identifies meeting/outcome tables and verbatim records. UN General Debate country pages returned a browser challenge in this expansion; no new General Debate PDFs are counted.
2. **UNFCCC national submissions and negotiating positions.** China and EU/member-state NDC PDFs were located in the [official registry](https://unfccc.int/NDCREG), but download responses failed PDF validation. They are not counted as acquired documents. Germany's listing points to a joint EU/member-state submission: it must not become an exclusively German target. Retry publisher access or obtain an official submitting-government copy.
3. **More German authentic QA and issue-matched ministerial evidence.** This is a higher priority than another unrestricted Chinese archive crawl, because the current response-training pool is imbalanced. The new Foreign Office material can supply evidence for reviewed questions, but generic articles must not be reclassified as authentic QA.
4. **Treaty-body government replies and national UPR follow-up.** Preserve the distinction between national submissions, committee findings, NGO submissions and recommendations by other states. Expand beyond the two acquired national reports only with source-role labels and cycle-aware splits.
5. **Larger multilingual UN corpora only for a diagnosed need.** [UPRPRC](https://github.com/mnbvc-parallel-corpus-team/UPRPRC) provides a reproducible UN document/alignment pipeline and released corpora, including a German-English subset. Its pipeline uses machine translation as an alignment intermediate; inspect the actual output schema and underlying-document terms before adoption. The bulk corpus was researched but not downloaded. It should not be labeled national persona data without speaker attribution.

## Files and reproduction

- `data/expansion_source_registry.json`: source purpose, languages, limitations and rights metadata.
- `data/manifests/expansion-20260913.json`: frozen URLs, local paths, hashes, parse outcomes and exclusions.
- `data/prepared/expansion-20260913/`: documents, authentic QA candidates, evidence passages, document families, PDF text, and the 100-record review packet.
- `data/prepared/expansion-20260913/un-parallel-eval/`: publisher dev/test sets, README and DISCLAIMER.
- `reports/expansion-20260913.json`: machine counts and artifact hashes; `expansion-un-parallel.json`, `expansion-review-packet.json` and `expansion-access-notes.json` supplement it.

From the repository root, a fresh checkout can replay the pinned country-source manifest:

```bash
python scripts/replay_expansion.py
python scripts/prepare_expansion.py
python scripts/prepare_un_parallel_eval.py
python scripts/make_expansion_review.py
python -m pytest -q
```

Use the existing project environment (`.venv/bin/python` locally). PDF extraction additionally requires Poppler's `pdftotext`. Replaying a live URL cannot guarantee historical bytes remain available: changed hashes deliberately fail. Preserve the private raw snapshot for exact recovery. Fresh collection uses `collect_expansion.py` (16 archive pages and 400-document limits; French required 64 pages), `collect_policy_documents.py`, and `collect_upr_national_reports.py`. The sampled German newsroom uses seed 42, 250 English candidate pages, and their publisher-linked German versions; the CMS-ID filter is only a discovery heuristic, never an event-date label.
