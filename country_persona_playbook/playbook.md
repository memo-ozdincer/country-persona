# Country-specific institutional persona post-training

**Implementation and data playbook · inspected 9 September 2026**

## 1. The decision

Build a **country-, institution-, issue- and time-conditioned representative**, not an undated national personality. A German government spokesperson, Germany’s national UN delegate, and a German official delivering a group statement are different roles. A speech in Chinese is not automatically Chinese policy. Preserve these distinctions in the data, model prompt and evaluation.

My recommended first experiment is one shared 4–8B instruction backbone, source-grounded supervised fine-tuning, and dated retrieval. Compare a shared country-conditioned adapter with separate country adapters. Keep the same evidence access, context length and inference budget across models. Start in one language; multilingual transfer is a separate experiment rather than a hidden confound.

Use three kinds of supervision together:

| Signal | What the model can learn | Best initial sources |
|---|---|---|
| Actual statements and Q&A | How to express a documented position and respond to questions | UN speeches; Chinese MFA Q&A; national missions; German Foreign Office press answers |
| Recorded decisions | Whether the represented country chooses the correct historical action | UNBench; official UN voting; UPR supported/noted responses |
| Evidence-grounded interaction | Whether the role persists and updates appropriately during a conversation | Constructed from dated briefs; SOTOPIA-π-style collection after the one-turn baseline |

**Do not begin with a large generic fictional-persona dataset.** Most of the value here is the source-backed institutional supervision. Role-playing datasets are construction/method precedents and optional auxiliary controls, not evidence about a country’s foreign policy.

## 2. What changed after deeper investigation

### 2.1 Real question–answer data are better than turning every speech into fake dialogue

The Chinese Ministry of Foreign Affairs Press Conferences Corpus reports **22,946 single-topic question–answer dyads**, covering October 2002 through December 2020 in English. It separates original transcript records into topic-specific pairs and documents spokesperson/date metadata. The paper was inspected; the actual Dataverse headers were blocked by a robot-check page. Source: [D09 paper](https://link.springer.com/article/10.1007/s11366-021-09762-3).

This should be a first acquisition request. Preserve original wording and parent-conference IDs. Do not use lemmatized text for language-model supervision. Treat it as official published public-response behavior, not a transcript of private government reasoning. Newer [official MFA transcripts](https://www.fmprc.gov.cn/eng/xw/fyrbt/) can extend the period, with deduplication against embassy mirrors.

Germany has official [government press-conference transcripts](https://www.bundesregierung.de/breg-de/aktuelles/regierungspressekonferenz-vom-4-september-2026-2451572). They contain multiple ministries, speaker labels and follow-ups. Filter the Foreign Office and relevant issues; do not assign every government answer to a UN persona. These are HTML pages, not a verified ready-made CSV corpus. Native German material and translations must remain linked, so a translation cannot leak into a different split.

### 2.2 UPR gives genuinely directed interactions

The [UPR Info database](https://upr-info-database.uwazi.io/en/library) identifies the recommending state, state under review, recommendation, topic and response. Its interface displayed 122,743 recommendations during inspection and provides a CSV-export control. This is a live UI count, not a downloaded corpus audit.

The useful task is **A recommends an action to B**, or **B responds to an incoming recommendation**, not an undirected bag of country-associated text. Incoming recommendations are not statements authored by the recipient. The UI’s `Date added` is ingestion time; use the review/session date for historical tasks. A supported/noted label is an official response category, not proof of implementation.

[OHCHR’s Universal Human Rights Index](https://uhri.ohchr.org/en/our-data-api) is an official complementary route with full JSON and Excel exports and API documentation available from its support contact. It covers UPR, Treaty Bodies and Special Procedures; only the relevant mechanism should enter a country-to-country dataset. Export links were found, but the files were not opened successfully. Record the schema after acquisition rather than inventing one from the UI.

### 2.3 Votes need the actual proposal—and careful sampling interpretation

The official [UNGA voting release](https://digitallibrary.un.org/record/4060887?ln=en), version 5 published in February 2026, documents **947,434 country-resolution rows** through December 2025. These are not 947,434 separate proposals. The release covers adopted resolutions decided by recorded vote and excludes failed drafts and paragraph votes. It cannot directly supply balanced adoption-versus-failure training.

Join each vote to its resolution/draft and a time-valid context. Keep non-voting distinct from abstention. The source specifically describes non-commercial use with attribution; keep that constraint in acquisition and distribution decisions.

### 2.4 Resolution text is available without reinventing PDF extraction

[CR-UNSC](https://zenodo.org/records/15154519) combines resolution, draft and meeting material with tabular metadata and citation-related variants. The latest release located was dated 22 December 2025 and extended through resolution 2798. It offers machine-readable formats; the [paper’s record](https://zenodo.org/records/15191558) describes 82 variables. The maintained code location is [Codeberg](https://codeberg.org/SeanFobbe/cr-unsc), not the archived GitHub mirror.

Use institutional documents as proposal/context evidence, not as a country’s own position. Citation relationships can help define hard holdouts, but grouping the entire citation graph into connected components may collapse too much into one giant component. Prefer adjudicated resolution families or topic-and-event lineages.

## 3. Acquisition priority

### P0: the first workable dataset

Acquire UNBench samples for integration, a UN speech corpus for scale, country-mission archives for grounded roles, the Chinese MFA corpus for natural QA, and UPR/UHRI for decisions and bilateral exchanges. Freeze UNBench/UNSC-Bench evaluation items before expanding training.

For a China/Germany comparison, use UNGA and UPR as well as UNSC material. [UNSC-Bench](https://aclanthology.org/2026.mme-main.10/) evaluates the permanent five; it is not a German benchmark. Do not create fictional German Security Council votes for years when Germany did not occupy that voting role.

### P1: broaden and update

The [UNSC Meetings and Speeches paper](https://academic.oup.com/jpr/article/63/4/735/8559606) describes over 160,000 statements from 1946–2024 and two TSV files. [UN Security Council Debates](https://arxiv.org/html/1906.10969v3) provides an overlapping 1992–2023 resource. Pick an initial extraction rather than blindly merging both.

The [UNGA Speech Corpus](https://www.linneaturco.com/research) expands beyond annual leader addresses into General Assembly proceedings. UNGDC is useful for long-run national priorities and language, but annual addresses are not interactive negotiation trajectories. The [documented UNGDC importer](https://raw.githubusercontent.com/un-project/un-extractor/main/scripts/import_gdebate_corpus.py) uses text files named by country/session/year; a precise date requires a metadata join.

### P2: new domains, not more of the same

[UNFCCC submissions](https://unfccc.int/process-and-meetings/the-paris-agreement/the-paris-agreement/cooperative-implementation/submissions-A6-2_A6-4_A6-8) add issue-specific negotiating positions. Preserve Party/coalition identity and publication date. They are an attractive cross-institutional or climate-topic evaluation pool, not guaranteed turnkey training rows.

The [UN Parallel Corpus](https://aclanthology.org/L16-1561/) is relevant to multilingual domain adaptation, not country stance. Generic RoleBench/OpenCharacter data can test role-following transfer but should not substitute for source-grounded national positions.

## 4. Papers and code to actually reuse

| Priority | Resource | Reuse | Do not assume |
|---|---|---|---|
| First | [TRL SFT + PEFT](https://huggingface.co/docs/trl/main/en/sft_trainer) | Simple, auditable supervised adapter baseline | Fine-tuning necessarily beats retrieval |
| First | [RoleLLM](https://github.com/InteractiveNLP-Team/RoleLLM-public) | Grounded role-specific instruction construction from source material | Fictional dialogue contains useful national-policy truth |
| After SFT | [Open Character Training](https://github.com/maiush/OpenCharacterTraining) | Source-backed persona preferences and persistence testing | Its generic character constitutions are ready delegation briefs |
| Interactive phase | [SOTOPIA-π](https://github.com/sotopia-lab/sotopia-pi) | Episode collection, expert/self-generated trajectories, filtering and agent-view SFT | A generic social-success rating measures authentic diplomacy |
| Evaluation | [UNBench](https://github.com/yueqingliang1/UNBench) and [UNSC-Bench](https://aclanthology.org/2026.mme-main.10/) | Task formulations, decision labels, baseline comparisons | Both cover Germany or provide unlimited uncontaminated training data |
| Ingestion | [un-extractor](https://github.com/un-project/un-extractor) and [CR-UNSC](https://codeberg.org/SeanFobbe/cr-unsc) | Official imports and document/metadata joins | Third-party automatic normalization has been validated here |

### Open Character Training: exact adaptation boundary

The official project uses constitution-conditioned preference generation followed by introspective supervised data. Its pipeline order is **DPO then introspective SFT**. Our simplest practical comparator is **source-grounded SFT then optional DPO**. That is an adaptation, not a faithful reproduction of the paper order.

Useful entry points are `character/distillation/{gen_prompts,teacher,student,data}.py`, `character/introspection/{self_reflection,self_interaction,data}.py`, and the model-specific shell scripts in `finetuning/distillation/`. The inspected distillation formatter imposes a 1,024-token filter. Long resolution examples need a deliberate context-length change; silently accepting that default could discard much of your data.

Keep the useful role-drift methodology, but replace personal-belief introspection with institutional duties, evidence use, represented entity and authorized updates. The role brief should not fabricate emotional identity, secret bargaining goals or unsupported commitments.

### SOTOPIA-π: the useful interaction method

The [published method](https://aclanthology.org/2024.acl-long.698/) uses behavior cloning and filtered self-interaction. The repo includes `data_generate/generate_conversations.py`, processing, training and human-evaluation directories, plus a QLoRA path. It also has older dependencies and Redis setup: treat it as a method/harness foundation, not an effortless drop-in package.

Build diplomatic tasks from source-backed scenarios, then filter on position fidelity, factual support, appropriate updating and goal validity. Do not optimize solely for agreement, stubbornness, or a generic judge’s assessment of persuasiveness. The correct national position can agree with another country or change after authorized new evidence.

## 5. Data architecture

Keep five layers separate:

```text
raw/         immutable originals + URL/version/hash/permissions record
canonical/   normalized source-backed events, still quarantined by default
splits/      frozen event-family, topic and time assignments
retrieval/   dated documents with scope and access rules
derived/     training-only prompt/completion or preference rows + provenance
```

An event record should identify who spoke, on whose behalf, in which institution, at what time and phase, using which source. Store country of speaker and represented entity separately. A group statement delivered by a German official may represent a coalition, not Germany alone.

Preserve source-specific identifiers alongside any country-code mapping. Historical entity and representation changes require explicit treatment rather than automatic relabelling to present-day countries. Prefer per-source mapping tables with validity intervals and unresolved cases quarantined.

A role brief is a compact, cited, time-bounded account of public positions. Store claims with source document IDs and validity dates, and distinguish direct source support from analyst inference. Current positions belong in updated retrieval/briefs; do not rely solely on fine-tuned weights as the current-policy store.

## 6. Constructing training examples

### Actual speech supervision

Input: represented country, date, institution, public proposal and relevant prior context. Target: the country’s actual statement. The target text must not appear in the retrieved input. Extracted speeches require phase labels—opening statement, national intervention, explanation of vote, procedural chair statement—before admission.

Do not fabricate a question and imply it was asked in the historical meeting. A synthetic question derived from a speech is a **synthetic instruction with a real source-backed answer**, a different provenance category from genuine QA.

### Genuine QA

Input: actual question, necessary prior exchange and date/role context. Target: the corresponding official response. Multi-topic splits stay in the same parent-conference group. Ambiguous follow-ups should not be trained without context. Press-conference examples can teach response behavior, but their institution remains labelled so the model does not confuse spokesperson authority with a UN negotiating mandate.

### Vote prediction

Input: a proposal and information available before the target vote. Target: the actual recorded vote category. No generated chain of thought is necessary. An explanation-of-vote is a separate task, with the known vote explicitly available if the task is post-vote explanation.

For the historical decision task, matching the recorded action is an observable label—not a judgment that the action was factually or morally correct. Country identity must contribute beyond an overall yes-vote prior.

### UPR interaction

Use a source-backed review scenario, recommending state, reviewed state and issue to model a recommendation. Predict the reviewed state’s official response to a given recommendation as a separate task. Do not present the response document to a model being tested on predicting that same response.

### Grounded synthetic examples

Ask a generator to produce a question only when an answer is supported by supplied passages. Retain source spans, generator version, prompt hash, validation status and whether the example is synthetic. Include cases where the right answer is to identify missing information, distinguish national from group positions, or defer to an authenticated updated brief.

Do not convert publicly expressed positions into invented private motivations. Include authenticity and independent factual support as different annotation dimensions: an official statement can make a contested or inaccurate claim.

## 7. Proposed pilot mixture and training

These numbers are design choices to test, not empirically established sample requirements. Start with a few thousand quality-controlled examples per country where available. Avoid manufacturing equal row counts through large volumes of weak synthetic text.

A starting **example-level mixture** could be 40% source-backed QA, 30% speeches/interventions, 20% votes or UPR actions, and 10% multi-turn/update/uncertainty examples. Row-level percentages do not equal supervised-token percentages. Log both, plus country/topic/year/source composition; long speeches must not dominate unintentionally. Reserve generic persona dialogue for an explicit optional ablation.

Use one shared instruction checkpoint, a single country-conditioned LoRA adapter, and completion-only SFT. Then compare separate country adapters at matched total training tokens and deployment budget. Separate adapters can make deployment convenient, but do not assume they represent a scientifically necessary architecture.

The starter’s one epoch, rank 16 and learning rate 1e-4 are smoke-test settings. Tune using development groups. Audit token lengths first; full UN resolutions may exceed short contexts. Use reviewed extracts or longer contexts, and do not truncate away the target or decisive proposal clauses. Measure per-task/country metrics, not only training loss.

### Optional mid-training

Only add shared diplomatic-domain adaptation if the baseline exhibits a domain/language deficit. Use raw original text with source/country/date headers and document boundaries. Exclude all held-out documents and derivative translations from mid-training as well as SFT. Compare against an equal-token SFT/retrieval baseline. Continuing training on undated speeches alone can learn a mixed historical average instead of an updateable role.

### Optional DPO

The [TRL DPO interface](https://huggingface.co/docs/trl/main/en/dpo_trainer) supports explicit `prompt`, `chosen` and `rejected` examples. Construct candidates for the same country, time, issue and evidence. A rejection should violate a documented stance, invent a commitment, drift into another role, or refuse an authorized update—not merely be less polished prose.

Do not make “another country’s answer” automatically rejected: countries often agree. Match candidates for length, evidence availability and writing quality where possible. Keep factuality and role fidelity separate. For SFT→DPO, make the reference policy the actual SFT model; disabling a lone SFT LoRA can revert to the original base, which is a different reference. Use a deliberate merged-SFT checkpoint or explicit reference-adapter arrangement.

RLVR is not the default solution to persona authenticity. Historical vote matching and output-format checks are executable labels; diplomatic fidelity and negotiation quality need source-based evaluation and human judgment. A judge model’s subjective score is not a perfect verifier.

## 8. Multi-agent harness

Store an episode log separately from training rows: scenario ID, timestamp, public state, per-agent private *authorized* brief, visible evidence, speaker/recipient/action and updated state. “Private” here means information specified by the experiment, not a fabricated claim about real confidential diplomacy.

For each training target, render the episode from that agent’s perspective. Other agents’ messages are context, not that agent’s desired output. Use one prompt/target transition per chosen turn, or verify masks in a full-conversation implementation. Avoid teaching a German adapter to produce the Chinese agent’s replies merely because both appear in the same transcript.

Initial protocol: opening position; response to another delegate; response to a revised proposal; final action. Later add context pressure, conflicting unauthenticated messages, and authenticated policy updates. Distinguish justified compromise from role drift. Do not score all disagreement as success or all agreement as failure.

Country identity should not be tied to a model vendor’s nationality. Keep the backbone constant to isolate post-training and role information. The [UNSC-Bench paper](https://aclanthology.org/2026.mme-main.10/) specifically studies diplomatic role assignment rather than treating model origin as role fidelity.

## 9. Evaluation and contamination controls

Core systems: country prompt; country prompt plus retrieval; shared country-conditioned SFT plus retrieval; per-country SFT adapters plus retrieval; optional preference-tuned and interactive variants. Keep evidence, decoding, tool access and token budget matched.

Report decision accuracy **and** class-balanced measures, calibration and per-country scores. For statements use source-supported position fidelity, unsupported-commitment rate, role attribution, and a blinded human-reviewed sample. Semantic/text overlap with the historical speech is not sufficient. For interaction, measure both persistence under irrelevant pressure and correct updating after authenticated changes.

Split whole events and resolution families before generating derivatives. All country votes and statements for a held-out event, translated copies, mission mirrors, paraphrases and synthetic QA derivatives should follow the parent group. Initial converter IDs are not full resolution-lineage reconciliation; draft/adopted symbols and annual renewals require a mapping pass.

For time-sensitive inputs record event date, publication date, validity interval and ingestion date separately. A same-day date alone may not establish pre-vote availability; use meeting sequence/time or conservative exclusion. Do not retrieve the target speech, later explanation of vote or a report announcing the outcome.

Three evaluation modes are different: source-conditioned reconstruction; policy inference from prior evidence; genuine temporal forecasting. Label them separately. Even a chronological post-training split cannot prove the base model never saw historical public documents during pretraining.

The provided code checks assigned groups and exact normalized long-text duplicates. It does **not** solve fuzzy/semantic duplication, erroneous group mapping, inaccessible source content, or pretrained contamination. It is a guardrail, not a certification of leakage-free evaluation.

## 10. Separate medical workstream

Keep the 70 RWTH cases described in the meeting notes outside training, synthetic generation, prompt selection, retrieval development and model selection. Preserve patient/source-group separation. No private RWTH data were accessed in preparing this package.

[PMC-Patients](https://github.com/pmc-patients/pmc-patients) supplies case summaries and retrieval relationships, not adjudicated oncology treatment targets. Its [metadata companion](https://huggingface.co/datasets/zhengyun21/PMC-Patients-MetaData) includes MeSH mappings that can identify candidate oncology articles for clinician review. Article topics alone are not eligibility labels.

For a treatment-prediction task, hide treatment and outcome information, including title leakage. Retain only information available at the decision time. Create a separate, clinician-checked decision target and evidence collection. Specialist personas should mean scope of expertise and evidence responsibilities, not artificial preferences for conflicting therapies. Compare multi-agent and single-agent systems at matched inference cost. This is a research evaluation design, not guidance for treating a patient.

## 11. Immediate work packages

**Data owner:** acquire D01/D02/D09/D14/D15, inspect headers and licences, snapshot source versions, and audit 50–100 records per source before scaling. Those are proposed audit sizes, not statistical guarantees. Complete country/entity/role and timestamp mappings.

**Training owner:** establish prompting/retrieval baselines, run the canonical conversion tests, audit tokenizer lengths/masks, and train the first shared adapter. Do not start all nine methods at once.

**Evaluation owner:** freeze event-family and temporal holdouts, define class-balanced vote and source-fidelity metrics, build a small expert-reviewed interaction suite, and guard both UN and medical evaluation manifests.

**Research question:** Does post-training improve authentic institutional decisions and multi-turn role behavior beyond a role prompt with the same retrieved evidence? The experiment should be useful even if retrieval wins and fine-tuning adds little.

## 12. Deliverable status

The registry distinguishes direct raw-schema inspection, paper documentation, importer-derived mappings and live-site inspection. Full corpora were not downloaded; several Dataverse/UN/Hugging Face endpoints were inaccessible. The package supplies locally tested converters and conservative review gates, plus an unexecuted GPU-training starter. Actual acquisition, rights approval, corpus-level quality checks and model training remain to be performed in the lab.

See `sources.csv` for every source URL, format, caveat and acquisition route; `methods.csv` for exact code entry points; `schemas.md` for data contracts; and `tests/test_results.txt` for the local test result.
