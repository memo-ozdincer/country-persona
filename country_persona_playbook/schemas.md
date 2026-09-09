# Data contracts: upstream formats vs our proposed formats

Inspected on 2026-09-09. JSON below is structural, not a real country-policy record. Source references correspond to `sources.json`.

## 1. Exact upstream formats inspected

### UNBench task 2: CSV + a separate draft

```text
Country,Original_id,Authors,Voting,Date
```

`Original_id` joins to a folder under `data/task2/<Original_id>/`. The inspected folder `2148` contains `S_2017_77-EN.json` and the corresponding PDF. The JSON fields are:

```json
{"Date":"<day month year>","ID":"<UN document symbol>","Title":"<draft title>","Authors":"<string>","Content":"<full draft text>"}
```

The CSV’s `Authors` is a serialized list-like string; the JSON’s `Authors` is a string. Do not assume the CSV cell is JSON; the converter does not need to parse it. Vote codes in this task are `Y`, `N`, `A`. The CSV alone does **not** contain the resolution text. Fail on missing/ambiguous draft joins.

Sources: [CSV](https://raw.githubusercontent.com/yueqingliang1/UNBench/main/data/task2.csv), [draft JSON](https://raw.githubusercontent.com/yueqingliang1/UNBench/main/data/task2/2148/S_2017_77-EN.json).

### UNBench task 4: JSON list with nested statements

```json
[
  {
    "Date":"<day month year>",
    "ID":"<document symbol>",
    "Title":"<title>",
    "Authors":"<string>",
    "Content":"<resolution text>",
    "Statements":[
      {"representative":"<speaker>","country":"<country label>","statement":"<speech>"}
    ]
  }
]
```

Flatten to one canonical row per statement while preserving the parent document group. The inspected sample includes post-vote statements. Do not automatically treat these as opening negotiation statements. `Authors` is not guaranteed clean penholder metadata.

Source: [task4.json](https://raw.githubusercontent.com/yueqingliang1/UNBench/main/data/task4.json).

### RoleBench: heterogeneous JSONL

The inspected Hugging Face schema exposes `role: string`, `question: string`, and `generated: list[string]`. Role-specific files add `type: string`. Load the intended `general` or `role_specific` file explicitly; the aggregate dataset loader reports a cast mismatch. Selecting a generated answer requires a quality policy, not blindly choosing the first string.

Source: [RoleBench card/viewer](https://huggingface.co/datasets/ZenMoore/RoleBench).

### Open Character Training: preference and SFT outputs

The official distillation formatter emits:

```json
{
  "chosen":[{"role":"user","content":"<prompt>"},{"role":"assistant","content":"<preferred response>"}],
  "rejected":[{"role":"user","content":"<same prompt>"},{"role":"assistant","content":"<other response>"}]
}
```

The introspection formatter emits `{"messages":[...]}`. This is the official project's data format, not a proposed UN-specific schema. We prefer explicit prompt/chosen/rejected for our derivative to make common context easy to audit.

Sources: [distillation formatter](https://raw.githubusercontent.com/maiush/OpenCharacterTraining/main/character/distillation/data.py), [introspection formatter](https://raw.githubusercontent.com/maiush/OpenCharacterTraining/main/character/introspection/data.py).

## 2. Documented formats—not directly downloaded and verified

| Source | What is established | What remains unverified |
|---|---|---|
| UNSC Meetings/Speeches | `meetings.tsv`, `speeches.tsv`; meeting, speaker, country and capacity metadata | Literal column names/types and release-specific missingness |
| Chinese MFA corpus | Q/A, dates, spokesperson, parent/split records and linguistic variants described by authors | File extensions, literal headers, encodings and licence |
| UPR Info | CSV export control; UI labels for recommending/reviewed state, recommendation, response and session | Export header names, types, completeness and licence |
| UHRI | Official full JSON/Excel export links and API access documentation | Export field names, nested layout and completeness of each mechanism |
| UNGDC | Importer reads `ISO3_session_year.txt` in `UNGDC_1946-2025.tar.gz` | Full release contents/count, exact speech dates and entity mapping |
| Official voting CSV | File/version metadata; importer reads `ms_code`, `ms_name`, `ms_vote`, `undl_id`, etc. | Direct official header/data verification in this environment |
| OpenCharacter | Two JSONL files: `synthetic_character.jsonl`, `synthetic_dialogue.jsonl` | Their record-level schemas; licence-tag/research-only conflict |

The registry links each exact documentation/importer source. A converter that guesses these uninspected headers is **not** provided. Use `prepare.py inspect` after acquisition, then pass explicit mappings for a QA CSV.

## 3. Our proposed canonical JSONL

One row = one source-backed target event/response. Every field is part of **our own proposed contract**, not an upstream UN schema.

| Field | Type / meaning |
|---|---|
| `schema_version`, `id` | Version and unique immutable record identifier |
| `source_id`, `source_record_id`, `source_url` | Dataset, upstream key and provenance |
| `source_version`, `raw_sha256`, `raw_file` | Snapshot identity and local original |
| `country_name`, `country_iso3` | Source label and reviewed code; code may initially be null |
| `represented_entity` | Entity actually represented; may differ from speaker nationality |
| `institution`, `speaking_capacity` | UNGA/UNSC/MFA/UPR/etc.; national delegate/chair/group spokesperson/etc. |
| `language` | Language of this text; translated variants need a shared parent group |
| `event_date`, `date_precision` | Day or year precision, never fabricated missing specificity |
| `phase` | Pre-vote, post-vote, public QA, annual address or reviewed other phase |
| `task` | Vote prediction, statement generation, QA or domain text |
| `group_id` | Conservative event/family split identity; reconcile across sources |
| `prompt_inputs.context`, `.question` | Information allowed in the model input |
| `target.text`, `.kind` | Desired continuation/label; not visible in retrieval |
| `evidence_ids` | Source identifiers for evidence snippets; empty until explicitly populated |
| `split` | train/dev/test/quarantine |
| `review_status`, `train_permission`, `approved_by` | Independent quality/permission approval and accountability |
| `source_verified`, `context_asof_verified` | Explicit provenance and historical-availability checks |
| `notes` | Exceptions and provenance decisions |

The actual emitted row has extension fields for speaker/draft provenance where relevant. The draft JSON Schema is in `config/canonical.schema.json`. It validates structure, not factual truth, permission sufficiency or absence of leakage.

## 4. SFT format to feed TRL

```json
{
  "prompt":[
    {"role":"system","content":"Research simulation of Example Republic's delegation. Date: 2020-05-01. Use the provided evidence."},
    {"role":"user","content":"[Reviewed dated context]\nHow does the delegation respond to this proposal?"}
  ],
  "completion":[
    {"role":"assistant","content":"[Source-backed response]"}
  ]
}
```

Use completion-only loss. This is particularly important for multi-agent dialogues: other delegates' turns belong in the target agent’s context, not in its supervised output. Store metadata in an aligned separate manifest, not inside the text the model learns to repeat. Source: [TRL SFT formats/masking](https://huggingface.co/docs/trl/main/en/sft_trainer).

The builder exports only approved training records and writes `train.sft.jsonl`, `train.manifest.jsonl`, `reviewed.canonical.jsonl`, and `audit.json`. It excludes domain-text records rather than pretending they are instruction data. For large raw corpora, add a streaming implementation after validating the schema; this starter loads canonical rows into memory.

## 5. Preference data for DPO

```json
{
  "prompt":[
    {"role":"system","content":"[Country, date, capacity and evidence rules]"},
    {"role":"user","content":"[Same proposal and evidence for both candidates]"}
  ],
  "chosen":[{"role":"assistant","content":"[Supported position without invented commitments]"}],
  "rejected":[{"role":"assistant","content":"[Comparable response with a specifically annotated position error]"}]
}
```

Maintain a preference manifest containing source IDs, violation type, evidence spans, reviewer, length audit and country/date/group. The structure is [TRL-compatible](https://huggingface.co/docs/trl/main/en/dpo_trainer); valid syntax is not evidence that the preference label is good. Preference generation and DPO training are specified but not implemented in the starter.

## 6. Optional mid-training format

```json
{"text":"<document country=\"XEX\" institution=\"UNGA\" year=\"2020\">\n[Original permitted text]\n</document>"}
```

This is a proposed derivative; use model EOS/document boundaries appropriately. Do not add date precision or missing authorship. Apply the same held-out-source and derivative exclusions as SFT. The kit parses UNGDC into canonical domain-text rows but does not train or automatically export a mid-training corpus.

## 7. Role briefs and episode logs

See `examples/delegation_brief.json` and `examples/episode.json` for **invented** structural examples. Claims should carry evidence IDs, validity periods and a direct-support/inference label. Episode events identify actor, recipient, visible evidence and action. A training renderer must produce the target agent's view without leaking other agents' experiment-defined hidden information. No claim is made to model real confidential government objectives.

## 8. Medical format, separate workstream

The [PMC-Patients author repo](https://github.com/pmc-patients/pmc-patients) documents a JSON list with `patient_id`, `patient_uid`, `PMID`, `file_path`, `title`, `patient`, `age`, `gender`, `relevant_articles`, and `similar_patients`. `age` contains value/unit pairs. The notes and article title may expose the eventual treatment/outcome. They are not tumor-board gold labels.

A proposed derived decision record would separate `case_before_decision`, `decision_time`, `specialty_role`, `available_evidence`, `clinician_checked_target`, `source_patient_group`, and `split`. The private RWTH 70 cases must remain evaluation-only, including their derivatives and any synthetic scenarios closely based on them. No medical conversion code is included.
