# France, UK, India and Brazil: data release

This release extends the project to the four requested countries with **substantive country evidence**, rather than another large collection of generic briefing language. It includes national strategies, trade-policy positions, climate commitments, public UN statements, historical decisions, economic context and source-backed policy applications.

Start with [the 12 actual policy applications](COUNTRY_EXTENSION_EXAMPLES.md). They show what the prepared data teaches and what a reviewer should inspect. These are authored candidates, not measured model answers or authentic historical Q&A.

## Fitness for a negotiating persona

The earlier preview overemphasized diplomatic phrasing. Authentic rhetoric alone does not supply the issue-specific preferences, constraints and choices needed here. This extension adds substantive evidence, but its 12 applications primarily demonstrate reading and preserving a stated policy. They do not yet train negotiation, reveal private bargaining limits, or demonstrate that changing the country changes a model's decisions appropriately.

The key missing unit is a dated **decision case**: the proposal actually on the table, the country's observable action, its attributed explanation, relevant material conditions, and any publicly stated conditions for agreement. The highest-priority next preparation work is to join resolution texts and explanations to recorded votes, build comparable cases across countries on the same issues, and attach dated bilateral dependencies and treaty obligations where they are relevant. A statistic alone must not be converted into an invented preference. Evaluation should reward justified agreement as well as justified disagreement between countries.

## What is available

| Layer | Delivered | Interpretation |
|---|---:|---|
| Newly acquired official documents | 40, across 17 document/event groups | Includes translations; not 40 independent national positions |
| PDF content | 1,546 pages across language versions | 36 PDFs, plus three HTML bodies and one GOV.UK speech object |
| Exact source passages | 2,221 | Retrieval and claim-review material, not automatically response targets |
| Explicit policy records | 12 | Three relevant to each new country; one is an EU collective position relevant to France and Germany |
| Authored policy applications | 12 | Questions, supplied evidence, target answers, references and inspection rubrics |
| Historical UNGA votes | 30,036: 7,509 per country | Newly prepared country views of the existing bulk download, covering 1946–September 2023 |
| UPR recommendations | 10,713 | Recommending speaker kept distinct from the state receiving the recommendation |
| UPR responses | 2,999 | Observed response labels attributed to the state under review |
| Other human-rights evidence | 5,266 | Institutional evidence, not a government's voice |
| Historical UNGA speech material | 1,483 upstream segments; 1,412 derived speaker spans | Two representations of overlapping material, not 2,895 independent speeches; covers 1993–2018 |
| Country-context cells | 240, of which 216 have values | Eight indicators, six countries, 2020–2024; missing values retained |
| Review packet | 80 items, 20 per new country | Decisions and reviewer names remain unset |

The extension's raw and prepared directories are `data/raw/country-extension-20260914/` and `data/prepared/country-extension-20260914/`. Source bytes stay private; code, manifests, curation definitions and reports are tracked in GitHub. This release uses **zero four-H100 node-hours** and launches no training job.

## Country coverage and substantive examples

**France:** The 2025 National Strategic Review in French, English and German; the 2025 Indo-Pacific strategy in French; the presidential transcript from the September 2025 Palestine-recognition conference; the fourth-cycle national UPR report in six UN languages. The EU's WTO government report is shared institutional context. Policy applications cover the European pillar within NATO, the limits of inferring exact nuclear-use thresholds from published doctrine, and correct attribution of the EU's collective emissions target. Sources: [SGDSN](https://www.sgdsn.gouv.fr/publications/revue-nationale-strategique-2025), [Indo-Pacific strategy](https://www.diplomatie.gouv.fr/files/files/priorites-et-actions/grands-dossiers/strate_gie_indopacifique_de_la_france_2025_cle0bc96b.pdf), [presidential transcript](https://www.elysee.fr/emmanuel-macron/2025/09/22/80e-session-de-lassemblee-generale-des-nations-unies-a-new-york-premiere-journee).

**United Kingdom:** The 2025 National Security Strategy, 2025 WTO government report, official large-print copy of the 2035 NDC, September 2025 UNGA statement and six-language UPR national report. Applications cover NATO's concrete role in defence planning, engagement with China alongside security measures, and the emissions target's baseline and aviation/shipping exclusions. Sources: [security strategy](https://assets.publishing.service.gov.uk/media/685ab0da72588f418862075c/E03360428_National_Security_Strategy_Accessible.pdf), [WTO report](https://www.wto.org/english/news_e/news_docs/g476_e.pdf), [NDC](https://assets.publishing.service.gov.uk/media/679b655f6bb4c44f0805e7bc/uk-2035-nationally-determined-contribution-large-print.pdf).

**India:** The government report for the 2021 WTO review, August 2022 cabinet announcement of its updated NDC, September 2025 external-affairs minister's UNGA statement and six-language UPR national report. Applications distinguish GDP emissions intensity from total emissions, installed non-fossil capacity from generated electricity, voluntary from mandatory waiver of WTO special treatment, and fisheries-subsidy disciplines from livelihood protections. Sources: [WTO report](https://www.wto.org/english/tratop_e/tpr_e/g403_e.pdf), [NDC announcement](https://www.pib.gov.in/Pressreleaseshare.aspx?PRID=1847813&lang=2&reg=48), [UNGA statement](https://pminewyork.gov.in/landnew?id=NTQ1Mg).

**Brazil:** The 2022 WTO government report, Portuguese 2024 NDC, FUNAG's 272-page compendium of foreign-policy positions for 2023–2024 and six-language UPR national report. Applications preserve the NDC's reduction range and baseline, distinguish Brazil's reported WTO waiver from its position on flexibility for other countries, and distinguish unilateral measures from Security Council sanctions in an attributed ministry statement. The compendium's individual excerpts have different speakers and dates; the book is not one speech. Sources: [WTO report](https://www.wto.org/english/tratop_e/tpr_e/g432_e.pdf), [Portuguese NDC](https://www.gov.br/mma/pt-br/assuntos/noticias/brasil-entrega-a-onu-nova-ndc-alinhada-ao-acordo-de-paris/ndc-versao-em-portugues.pdf), [FUNAG compendium](https://funag.gov.br/biblioteca-nova/produto/loc_pdf/1299/1/repertorio_de_politica_externa%3A_posicoes_do_brasil_2023-2024).

Eight source languages are present: English, French, German, Portuguese, Arabic, Chinese, Russian and Spanish. Most of the six-language coverage comes from four UPR reports. This is not eight equally broad corpora, and there is no new Hindi corpus. Eleven of the 12 policy claims use a national source; one uses an EU source. The authored answers are English, including two applications grounded in Portuguese passages; these paraphrases are labeled as assistant-authored, not official translations.

## What the country facts mean

The World Bank context layer covers population, nominal GDP, trade/GDP, agriculture/GDP, manufacturing/GDP, net energy imports, renewable electricity output and military expenditure/GDP. Definitions, original source organizations, units, JSON pointers and raw-file hashes are retained. There are 18 missing renewable-electricity cells and six missing net-energy-import cells; missing is not zero. [World Bank indicator metadata](https://datahelpdesk.worldbank.org/knowledgebase/articles/898599-indicator-api-queries).

These are 2020–2024 observations from the database vintage retrieved in September 2026, not the information set available in those historical years. They provide material context. For example, a trade/GDP value is neither bilateral dependence on China nor evidence of support for a particular sanction. The pipeline does not turn those statistics into inferred national preferences.

## Provenance, dates and splits

Every document retains its publisher URL, original bytes, SHA256, language, represented entity and extraction method. PDF passages preserve exact character offsets and page numbers. The 12 authored policy records have exact evidence spans and source hashes; supported claims and generated applications are separate files.

Issue dates, policy reference dates, publication dates and retrieval dates are distinct. India's WTO report was issued on 25 November 2020 for a 2021 review. The UK report describes policy as of July 2025 but was publicly released for its October review. French strategy translations cannot be assumed available on the original French release date. France's English UPR report has a 2023 issue date with later production codes. The Brazilian compendium's coverage years cannot date all excerpts or establish publication availability. Unknown availability remains unknown.

The new canonical records all have `split=quarantine` and `training_admitted=false`. Proposed splits are supplied separately. Translation/document groups, shared document symbols, parent relationships and long exact duplicates remain together; known prior split allocations are protected. UPR cycle 3 remains development and cycle 4 remains test. **33,253 new canonical rows overlap prior training event groups**, usually because the same UN meeting or UPR document contains multiple countries. They are additional country views, not fresh test events. No new record is automatically declared a clean evaluation item.

The existing speech and UPR parsers now accept explicit country mappings. Their default China/Germany focus remains unchanged. The UK’s long UN seat name is mapped without dropping its original label. Original and amended vote labels remain separate, and a mixed UPR response such as `Supported/Noted` is preserved.

## Why this preparation matches the task

| Choice | Basis | Scope of the inference |
|---|---|---|
| Extract attributable public positions rather than national personality adjectives | [UN General Debate Corpus paper](https://arxiv.org/abs/1707.02774) | Public diplomatic text can inform expressed preferences; it does not reveal private motives or a population's character. |
| Keep evidence documents separate from authored response targets | [RAFT](https://arxiv.org/abs/2403.10131) | Evidence-conditioned adaptation is a relevant experiment. This is not a reproduction of RAFT's full chain-of-thought recipe. |
| Use conversational prompt/completion exports for a small SFT experiment | [TRL 0.24 SFT documentation](https://huggingface.co/docs/trl/v0.24.0/sft_trainer) | Compatible with the repository's completion-only training workflow; the format itself does not establish data quality. |
| Keep Qwen3 thinking disabled and test the actual template | [Qwen3-8B model documentation](https://huggingface.co/Qwen/Qwen3-8B) | The CPU preflight checks that prompt tokens are a prefix of the full example and that target tokens remain. |
| Group translations and old events before allocating examples | [Cross-language contamination](https://aclanthology.org/2024.emnlp-main.990/), [deduplication](https://arxiv.org/abs/2107.06499) | These checks address known leakage routes; they are not complete semantic deduplication or proof of absence from base-model pretraining. |
| Test conditions, dates, shared positions and category errors | [CheckList](https://aclanthology.org/2020.acl-main.442/), [FActScore](https://aclanthology.org/2023.emnlp-main.741/) | Task-specific behavioral and claim-support checks are more useful than country-name classification alone. |

The 2,800-character passage cap, purposive source selection, 12 demonstrations and 80 review items are project engineering choices, not literature-prescribed optimal values. Routine ministry wording does not qualify as useful supervision merely because it is authentic. Votes without their proposal text are retained as action data and are not exported as free-form persona answers.

## Training compatibility and inspection milestones

The 12 demonstrations are also exported as conversational `prompt`/`completion` candidates with `chat_template_kwargs={"enable_thinking": false}` and aligned integrity manifests. Eleven have proposed training-family placement; the compendium-derived example remains in the quarantine bucket until its availability/family treatment is resolved. None is admitted. These exposed examples must not be repackaged as a hidden evaluation set.

The cached Qwen3-8B tokenizer verified all 12 examples on CPU: **3,914 sequence tokens in total, maximum 438 per example**, with nonempty completions and correct prompt boundaries. That establishes format compatibility, not model quality. Twelve examples are a demonstration, not a sufficient adaptation corpus. The [token preflight](../reports/country-extension-token-preflight.json) includes supervised-token counts and tokenizer hashes.

The next experimental milestones remain small and diagnostic:

1. Inspect the 80-item packet: attribution, substantive content, source extraction, qualifiers, dates and splits. The packet includes three policy claims and three corresponding applications per country, plus recommendations, responses, speech boundaries, votes, statistics and source passages. Items sharing evidence are not independent observations.
2. Create an independent issue-matched evaluation set. Check legitimate disagreement and agreement, metric/baseline errors, unsupported commitments and source changes. Include country-name-masked and language-switched variants. The 12 demonstrations provide examples of rubrics, not a completed benchmark.
3. Compare the unchanged Qwen3-8B with country prompting against prompting plus reviewed evidence. Only then build a balanced, larger LoRA training subset if errors suggest adaptation could help. Retain the existing four-H100 workflows and [measured compute plan](POSTTRAINING_PLAN.md); no new GPU reservation or run is part of this data release. A new wall-time estimate should use the final selected token count and measured cluster throughput.

## Exclusions and remaining limitations

Six registered acquisitions are excluded: the Brazil defence PDF, India's foreign-ministry annual report, three direct UNFCCC NDC PDFs, and the Brazilian UNGA speech at its MRE URL. Reasons include login requirements, a removed URL and challenge HTML. The UK and Brazilian NDCs were recovered from official national copies; India's cabinet announcement is explicitly an announcement, not the full NDC. An additional Planalto attempt redirected to login and is recorded separately. The FUNAG file began with a newline before its PDF header; validation was corrected and Poppler parsed it successfully. No access control was bypassed. [Access notes](../reports/country-extension-access-notes.json).

The collection is not exhaustive. It lacks complete bilateral trade/energy dependency matrices, treaty/coalition membership histories, joined resolution text for most votes, and broad independent policy implementation assessments. The vote archive ends in September 2023; later policy documents are not evidence of later recorded votes. The dated WTO comparison must not be read as proof that a government's older position remains current. Public source access is not marked as a blanket training or redistribution permission; source-use review remains explicit. No independent expert content audit or model-quality evaluation has been completed for this release.

## Files and reproduction

- [Source registry](../data/country_extension_registry.json): selected documents, institutional roles, dates and language families.
- [Frozen manifest](../data/manifests/country-extension-20260914.json): raw hashes, collection outcomes, context metadata and previous split-ledger hashes.
- [Preparation report](../reports/country-extension-20260914.json), [curation report](../reports/country-extension-curation.json), [review packet report](../reports/country-extension-review.json).
- [Position and application definitions](../data/curation/country_extension_positions.json): the actual authored claims, questions, answers, anchors and rubrics.

With the prior bulk snapshots and split ledgers restored, run from the repository root:

```bash
.venv/bin/python scripts/replay_country_extension.py
.venv/bin/python scripts/prepare_country_extension.py
.venv/bin/python scripts/curate_country_extension.py
.venv/bin/python scripts/make_country_extension_review.py
.venv/bin/python scripts/check_country_extension.py
.venv/bin/python -m pytest -q
```

Poppler's `pdftotext` and the existing Python data dependencies are required. The checker also needs the cached Qwen3 tokenizer; use `--tokenizer PATH` for its equivalent location. A publisher hash change fails replay rather than silently changing the dataset. Fresh discovery is separate: `collect_country_extension.py` and `collect_country_context.py` obtain a new live snapshot. The frozen release cannot guarantee that publishers retain old bytes, so preserve the private raw directories.

Preparation verified source bytes, archive extraction, canonical schemas, unique IDs, exact evidence spans, prior event-family protection and proposed cycle holdouts. Manual visual inspection included Brazil's NDC target table on PDF p. 36 and India's WTO provisions on p. 17. This is not a claim that all 1,546 pages or all languages were manually reviewed.

The private raw and prepared release has been copied to `/scratch/memoozd/persona` on Trillium: **176 files, 174,883,063 bytes**, with every transferred file checked against its local SHA256. See the [transfer verification](../reports/country-extension-trillium-verification.json). This was a data transfer and CPU verification, not a GPU run.
