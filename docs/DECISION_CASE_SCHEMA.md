# Decision case schema, version 1.0

Owner: Memo Ozdincer. The representation distinguishes observable actions, attributable claims and missing information.

| Field | Meaning |
|---|---|
| `id`, `schema_version` | Stable case identity and representation version |
| `country_iso3`, `represented_entity` | Which national institution is represented |
| `event_date` | Date of the observed final decision |
| `proposal_symbol`, `proposal_evidence` | Actual draft under consideration, with source URL, text hash, character offsets and PDF pages |
| `resolution_symbol` | Adopted resolution; not a substitute for identifying the draft or individual vote |
| `observed_action`, `amended_action`, `vote_evidence` | Original final vote, amendment and independent primary roll-call reference |
| `public_explanation`, `explanation_kind`, `explanation_evidence` | Attributed paraphrase, statement type and exact source support; missing is explicit |
| `stated_considerations` | Concerns stated by the representative, not independently proven causal drivers |
| `requested_changes` | Publicly requested wording or policy changes, not automatically binding conditions |
| `conditions_for_agreement`, `conditions_status` | What conditions are actually demonstrated; unknown remains null |
| `material_context`, `missing_context` | Dated contextual evidence and the remaining gaps; later statistics must not be presented as contemporaneous knowledge |
| `group_id`, `related_group_ids` | Meeting and decision links for leakage/split control |
| `use`, `split`, `training_admitted`, `fresh_evaluation_eligible` | Research use and admission; all initial cases are exposed retrospective demonstrations |
| `author`, `derivation`, `review_status` | Project ownership, assistant-prepared derivation and pending independent review |

Future additions should distinguish externally measured dependencies, government assertions and analytical hypotheses. Do not encode a negotiating threshold or private motive unless the evidence supports it. Keep pre-vote information separate from post-vote explanations before attempting any forecasting evaluation.
