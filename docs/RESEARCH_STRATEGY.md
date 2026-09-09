# Data and experiment strategy

The target is a **dated institutional representative**, not the average citizen, a national personality, or a model claiming official authority. The research question is whether post-training improves documented positions and observable decisions beyond prompting with the **same evidence**. Public diplomatic discourse provides evidence of public positions; it does not reveal secret negotiating preferences.

## Recommended order

| Stage | What it tests | Data from this repository | Decision to advance |
|---|---|---|---|
| 0. Prompted base model | What is already available without adaptation? | Locked evaluation examples and dated evidence | Record country/task/language baselines before tuning |
| 1. Same model + dated retrieval | Does missing evidence explain the error? | Mission statements, conference transcripts, UHRI institutional evidence | Retain identical retrieval packets for all later comparisons |
| 2. Shared country/institution-conditioned SFT | Does response training add value? | Genuine MFA and German Foreign Office Q&A; carefully selected national statements; observed UPR actions | Improve held-out position/action fidelity without unsupported commitments or poorer general capability |
| 3. Per-country adapter comparator | Does parameter separation help? | Same parent data, budgets and base model as stage 2 | Prefer shared adapter unless separate adapters measurably help |
| 4. Grounded preferences, if needed | Does the model drift, invent commitments or mishandle updates? | Reviewed error pairs tied to dated evidence | Use DPO only after diagnosing these errors; match lengths and avoid country-name shortcuts |
| Optional domain adaptation | Is there a persistent domain-language deficit? | Cleaned historical speeches and institution-authored text, with eval families removed | Compare added pretraining with an equal-compute SFT control |
| Future project: interactive training | Does behavior persist and update during negotiation? | Evidence-linked briefs, authentic follow-ups and country-to-country UPR records | Build the simulator only after the single-agent baseline is convincing |

Start with a modest one-epoch LoRA pilot and a tokenizer/10-step smoke run. Do not reserve thousands of GPU hours for a recipe before measuring learning curves. Sweep data sizes (e.g. 250, 1,000, then the available admitted pool per country) before increasing epochs or model scale. These are experimental choices, not paper-proven sample requirements. Log GPU-hours, wall time, supervised tokens and examples separately. The provided multi-GPU script is an implementation starting point, not a measured throughput or memory claim.

## What the literature supports—and what is our adaptation

1. **RoleLLM / RoleBench** motivates role-conditioned instructions and role-specific knowledge construction. We adopt the conditioning and grounding idea; fictional-character data are not evidence of national policy. Genuine observed answers are preferable when available. [Wang et al., Findings of ACL 2024](https://aclanthology.org/2024.findings-acl.878/).
2. **LoRA / QLoRA** provide economical adaptation mechanisms, not proof of persona fidelity. Ordinary LoRA is the primary multi-GPU recipe; QLoRA is a single-GPU memory-saving alternative here. [LoRA](https://arxiv.org/abs/2106.09685), [QLoRA](https://arxiv.org/abs/2305.14314).
3. **DPO** provides a direct preference objective without training a separate reward model. It needs justified pairs, not an arbitrary preferred country answer. A response from Germany can also be correct for China on an issue where their positions coincide. [Rafailov et al.](https://arxiv.org/abs/2305.18290).
4. **Open Character Training** is relevant to persona persistence. Its original constitutional preference training followed by introspective SFT is not reproduced by our SFT-first plan. A cited, dated delegation brief would replace personality traits. We deliberately avoid inventing officials' inner beliefs. [Maiya et al.](https://arxiv.org/abs/2511.01689), [author code](https://github.com/maiush/OpenCharacterTraining).
5. **SOTOPIA-π** motivates behavior cloning and filtered interaction learning in the future simulator. Its social-goal metrics are not diplomatic ground truth; the paper also reports weaknesses in LLM-based evaluation. Use independent evidence checks and human adjudication, not agreement-seeking as the reward. [Wang et al., ACL 2024](https://aclanthology.org/2024.acl-long.698/).
6. **Don't Stop Pretraining** supplies evidence that continued domain/task pretraining can help in its studied settings. Applying that result to modern instruction-model country personas is a hypothesis requiring an ablation, not an established recipe. Raw UN resolutions teach institutional language, not the preferences of their constituent countries. [Gururangan et al.](https://arxiv.org/abs/2004.10964).
7. **UNBench** offers institution-specific drafting, voting and statement tasks. We acquired the GitHub sample at a pinned commit, retain it as evaluation material, and do not call it the full release. Its draft join is necessary for vote inputs. [Liang et al.](https://arxiv.org/abs/2502.14122), [author repository](https://github.com/yueqingliang1/UNBench).

No cited study establishes “perfect” country personas, nor proves that more persona-consistent prose improves downstream UN-like collective decisions.

## Training objectives matched to data

**Authentic response SFT.** Input the country, institution, date, language, actual question and necessary prior turns. Target only the named spokesperson's answer. The Chinese archive publishes edited English records; the German archive supplies German transcripts with explicit ministry labels. A Foreign Office answer is not interchangeable with a UN ambassador's statement. Preserve the role tag during training and evaluation. Use completion-only loss so earlier speakers' turns remain context. [Pinned TRL SFT interface](https://huggingface.co/docs/trl/v0.24.0/en/sft_trainer).

**Statement reconstruction.** Mission statements and extracted UNGA speaker spans supply documented wording, but a title alone rarely determines the entire response. These candidates are explicitly labeled reconstruction. Before relying on them for position learning, curate an admissible brief or issue-specific instruction supported by the document; never put the target speech into a “retrieval” input and report the result as forecasting. Speech imitation should be a smaller auxiliary objective, not the whole persona dataset.

**UPR actions.** A recommendation is authored by the recommending state; a response belongs to the state under review. Preserve `Supported`, `Noted` and `Supported/Noted`. The latter is not silently collapsed. Support is not implementation. Some records have missing or multiple originators or response labels; those stay evidence/candidates requiring resolution. OHCHR document publication and index ingestion dates are not review-meeting dates. The current candidates support retrospective response reconstruction; a prospective prediction task needs earlier context and a verified decision cutoff.

**Historical domain text.** UNGDC and raw UNGA segments can support domain adaptation after cleaning and event-family exclusion. Pre-1971 records labeled China must not become PRC supervision. Pre-reunification West Germany is a distinct temporal entity. The author website snapshot and the latest Dataverse release have different coverage. Dates ending in `0101` in the Speaking Volumes filenames are not accepted as exact meeting dates.

**Grounded preferences.** Collect actual SFT errors. Pair a corrected response with the faulty one only when the preference is justified by source evidence: misattribution, invented commitment, contradicted position, unsupported refusal to update, or role drift. Preserve parent/event splits, judge provenance, generator version and source IDs. Keep language, length and style comparable. Use a blinded human sample to estimate judge error. No synthetic preference corpus is fabricated in this delivery.

**RL.** Do not start with a learned reward for diplomatic style or generic “negotiation success.” Sparse recorded votes can support a verifiable action objective, but reward optimization cannot repair missing proposal context or label contamination. Consider online RL only after rewards correlate with independently adjudicated behavior, and after a DPO or filtered-SFT comparison. A new method is not justified just by available compute.

## Evaluation and sampling

- Keep the underlying checkpoint, model revision, evidence, decoding budget and scoring protocol fixed across prompt-only, retrieval, shared-adapter and per-country-adapter comparisons.
- Report authentic QA, statement reconstruction, recommendation generation and action prediction separately. Never use speech similarity as the sole position-fidelity score.
- Use macro-F1, balanced accuracy, class counts and calibrated class probabilities for action tasks. Country-majority and always-support/always-yes baselines are necessary. Country-level observations from one review or resolution are correlated; bootstrap entire event groups, not individual rows.
- Have reviewers assess source support, attribution, unsupported commitments, appropriate uncertainty, and justified updates. Preserve the difference between maintaining a documented position under irrelevant pressure and accepting a verified policy update.
- Temporal holds are grouped before derivatives. Exact long-text mirrors, parents, document symbols and adjudicated families cannot cross splits. UPR cycle holdouts are distinct from calendar holdouts; the build config records both.
- Add a held-out topic/family set after grouping recurring resolutions manually. Exact matching and keyword topics are useful diagnostics, not semantic decontamination.
- Language is a confound: English Chinese Q&A versus German German Q&A does not isolate a country effect. Report language-specific results; use English mission statements as a common-language comparison. If translating, preserve the original and group both versions together, label the translator and audit political terminology.
- Existing historical text may already be in model pretraining. Do not call historical reconstruction an uncontaminated forecast. Use genuinely new, dated events for a separate prospective evaluation.
- Use balanced **country × institution × task** sampling after cleaning. Log token shares too; long speeches can dominate loss even when their row share is small. The old 40/30/20/10 mixture is a hypothesis and is not imposed on the acquired pool.

## Source work to prioritize next

1. Resolve source-level reuse decisions and review sampled Q&A boundaries, coalition labels and policy dates. Expand confidence-based batch admission only after measuring parser precision.
2. Complete the remaining UNGA speech meeting-date joins and add agenda items. The current pipeline already joins uniquely matched UNGA-DM meeting dates with provenance; unmatched segments and upstream year conflicts remain flagged. Review the speaker-boundary rules before admitting these candidates.
3. Join UPR response timing and prior national reports/advance questions. The acquired labels are valuable, but current issue labels and recommendation text alone do not determine the reviewed state's decision.
4. Acquire the official UNGA/UNSC vote releases and proposal texts together when their empty download endpoints become accessible. Keep non-voting separate from abstention and failed drafts separate from adopted-only sampling.
5. Revisit the CMFA bulk Dataverse corpus, the UNSC speech corpora, CR-UNSC and the full UNBench archive. Access failures are logged, not treated as absent data. Use the original source registry for remaining candidates; the medical workstream is outside this repository's build.

## Additional sources found during this build

**UNGA-DM** (Fjelstul, Hug and Kilby) provides an accessible research-database alternative while the official bulk CSV endpoint returns an empty body here. The downloaded vote extract has 1,205,730 country-decision rows across 7,509 decisions, dated 1946–2023 in the actual file. The linked codebook is an older description; the observed extract coverage is recorded separately. Original and amended votes, non-voting statuses, decision types, draft IDs and meeting dates are retained. These labels are not exported to vote-prediction SFT without proposal text. Meeting IDs also allow explicit date joins to the speech corpus. [Publisher](https://unvotes.unige.ch/), [codebook](https://unvotes.unige.ch/download_file/1/1).

**Estimating the Geopolitical Preferences of Large Language Models from United Nations Voting Data** (Chupilkin, July 2026 preprint) is a useful evaluation extension. It uses a dynamic ordinal ideal-point approach and highlights how raw agreement can be dominated by support rates and agenda composition. Its elicitation asks models to evaluate proposals without a national role, so it is not evidence that country-persona tuning works. The paper says replication data will be released upon publication; they are not counted as acquired. A future evaluation can compare actual country-conditioned decisions and baseline marginal preferences, while treating latent-position estimates as assumption-dependent. [Paper](https://arxiv.org/html/2607.25526v1).
