# Data dictionary and preparation rules

## Layout

- `country_persona_playbook/`: supplied kit, preserved unchanged.
- `data/raw/`: acquired source files, publisher metadata, collection manifests and per-file SHA256 receipts. Large and third-party files are local and Git-ignored.
- `data/sources.lock.json`: tracked list of exact source URLs, local paths, hashes and sizes; use for verification/reacquisition.
- `data/canonical/`: source-specific JSONL with literal source text and provenance. The full UNGA speech corpus is normalized; OHCHR is normalized for rows involving China/Germany while its complete source export remains raw.
- `data/prepared/pilot/pilot.canonical.jsonl`: country-focused pool with event splits and quality flags, including evidence-only documents.
- `data/prepared/pilot/candidates/COUNTRY/TASK/{train,dev,test}.sft.jsonl`: conversational candidates, accompanied by row-aligned manifests. They are not automatically rights-cleared or expert-adjudicated.
- `data/prepared/pilot/review/admission.csv`: reviewable record list. Candidate exports remain useful for inspection; the training entry point requires explicit admission decisions.
- `data/index/`: optional dated local evidence index.
- `reports/`: measured counts, exclusions, parse failures, quality findings, tests and source status.

## Canonical schema v2

| Field | Meaning |
|---|---|
| `id`, `source_record_id` | Stable source-prefixed row identifier and original/derived key |
| `source_id`, `source_url` | Acquisition source and source page; not necessarily an individual official document |
| `raw_file`, `raw_sha256` | Actual local source file and byte hash; derived text always retains its source |
| `parent_id`, `derivation`, `source_char_span` | Lineage; spans are half-open offsets into the parent text where provided |
| `country_iso3`, `country_name` | Explicitly mapped country or null if unresolved; original source codes stay separate |
| `represented_entity` | National state, coalition, historical entity or non-state mechanism |
| `institution`, `speaking_capacity`, `speaker` | Venue/role and named speaker where available |
| `language` | Language of the text used by the pipeline; not necessarily original spoken language |
| `event_date`, `date_precision` | Day, year, or unknown. Precision is never fabricated |
| `available_date` | Conservative known publication/index date where available; null excludes a document from dated retrieval |
| `group_id`, `split_group`, `document_symbols` | Source event and joined leakage-control component |
| `task`, `title`, `question`, `context`, `history`, `text` | Task type, input material and literal target/document text. `text` is not always an SFT target |
| `topics`, `topic_method` | OHCHR labels or explicitly weak keyword categories; not positions or stances |
| `quality_flags`, `quality_status`, `review_status`, `rights_status` | Machine findings and unresolved/admitted status; do not interpret parsed as expert-approved |
| `split` | train/dev/test/quarantine after component-level assignment |
| `reviewed_states`, `recommending_states`, `response_labels`, `upr_cycle`, `upr_session` | Directed UPR relationship, retained exactly from OHCHR |

## Inspected upstream formats

**OHCHR full JSON** is a list of objects with `AnnotationId`, `Symbol`, `Text`, `DocumentId`, `PublicationDate`, `AnnotationType`, `Countries`, `AffectedPersons`, `Themes`, `Sdgs`, `UprPositions`, `UprSession`, `UprRecommendingCountry`, `UprCycle`, `UprRecommendingRegions`, `Regions`, `PublicationDateOnUhri`, `Body`. Some `Text` values contain HTML. The parser removes presentation markup while preserving the original JSON in raw storage. Only UPR entries with originators are used as country recommendations; other mechanisms remain evidence. Mixed response labels are retained.

**Speaking Volumes** is an RData object named `txtstatesyears`, with 32,366 rows and columns `doc_id`, `text`, `country`, `meeting`, `session`, `year`, `stateabb`, `words_spoken`. The country code column is not ISO3. The archive also contains `topic_scores.RData` and `unga_word_vectors.RData`; these are preserved but are not persona text. The pipeline keeps all original segments and makes separate China/Germany speaker-span derivatives only when a literal country-labelled speaker marker is found. These boundaries still need review.

**Chinese MFA HTML** supplies `ArticleTitle`, `PubDate`, a `.content_text` body, bold outlet/question labels and spokesperson-prefixed answers in the inspected archive. Each conference yields a full transcript plus answer rows; earlier exchanges stay in the same parent group. Layout failures are reported. The corpus consists of public English renderings, not recordings of private deliberation.

**German conference HTML** has speaker headings with class `Rednerkopf`; ministry labels include `(AA)` for the Foreign Office. Only an AA answer following a question/follow-up becomes a foreign-policy QA target. All prior speakers are labeled context. An AA opening announcement is not turned into an invented question-answer pair.

**Mission HTML** uses publisher-specific body containers. National and detected coalition statements remain separate. Date differences between title, archive and publication are explicit flags. Unknown venue, group identity, and publication-as-event proxies are reviewable. The classifier intentionally does not treat alignment with an EU statement as authorship on behalf of the EU.

**UNGDC public author database** exposes country/session/year plus speech detail pages. The accessed snapshot is through 2022; it is not the newest Dataverse release. China includes historical representation before 1971; those rows are quarantined for PRC work. Exact dates remain unknown, so these are historical domain/evidence records, not dated retrieval documents.

**UNBench sample** has a task-2 vote CSV joined through `Original_id` to a unique draft JSON; task-4 statements are nested under parent documents. The acquired commit, all downloaded files and raw draft joins are retained. It is a sample benchmark, not a training corpus.

## Quality stages

1. **Acquired:** nonempty bounded download, immutable receipt, source provenance.
2. **Parsed:** source layout/schema validated; unexpected layouts produce explicit failures.
3. **Candidate:** correct focus-country role, permitted task type, no detected coalition/parse blocker, not quarantined, within configured character selection limits. This is a data selection stage, not a legal or expert approval.
4. **Admitted:** a review ledger records quality and scope-of-use decisions with reviewer and reason. No decision is inferred from public access or a paper's license.
5. **Tokenizer-ready:** model-specific chat template preserves the prompt prefix, targets fit the context window, completion token counts are measured. Character counts do not certify GPU readiness.

Candidates with long necessary history are excluded from the short-context pool without truncation. Their full records remain canonical. No conversation is cut into misleading fragments to hit a target row count.

## Added UNGA-DM vote extract and meeting-date joins

The acquired `votes.csv` contains `decision_id`, `member_state_id`, `member_state`, `original_seat_name`, `current_seat_name`, `original_vote`, `amended_vote`, `vote_was_amended`, `session_id`, `meeting_record_id`, `page_number`, `draft_resolution_id`, `resolution_id`, `decision_mode`, `decision_topic`, `important`, `request_by`, `meeting_number`, `resumption_number`, `meeting_date`. `decisions.csv` retains all downloaded decision metadata, including non-recorded decisions.

The focus canonical file preserves China, Republic of China, Germany, West Germany and East Germany as distinct source entities. Current PRC and post-reunification Germany are not silently extended backward onto the other historical governments. `not voting` and `not voting (suspended)` are distinct from `abstaining`; original and amended votes remain separate. This is `vote_label_only` data until full proposal context is joined.

Speaking Volumes meeting IDs are joined to unique dates observed in UNGA-DM. Each successful join records the supporting vote-file hash. Conflicts with the upstream year are flagged; unmatched rows keep year precision. No exact date is inferred from the sometimes-placeholder filename. The meeting-date join improves metadata, but does not certify all speech segmentation or make a post-vote statement usable as a pre-vote forecast.
