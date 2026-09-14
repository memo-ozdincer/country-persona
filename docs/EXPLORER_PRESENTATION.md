# Country overview and training format

The landing page shows one country selector, a characteristic policy application, counts by type, and four annotated sections of the training record. The original searchable catalog remains at `advanced.html`.

## Fix for the Ukraine-only view

The former comparison-first presentation selected twelve linked country–decision cases for two Ukraine resolutions. That small subset was correctly stored but misleading as a view of the entire collection. Legacy `#view=compare` landing-page links now open the country overview. The secondary comparison page explicitly names its limited coverage. Specific record, type and file links still open the full catalog.

The six featured examples are China’s development-cooperation conditions; Germany’s critical-input dependencies and continued cooperation; France’s European defence priorities within NATO; the UK’s 2035 climate target; India’s fisheries-subsidy qualifications; and Brazil’s dated WTO special-treatment position. These are purposively selected illustrations of policy content, not statistically representative samples or model outputs. Other authored applications remain expandable under each country.

## Counts

The overview counts distinct `record_id` values within each record type and country across indexed releases. This collapses repeated serialized versions and excludes review/lineage objects from the displayed table. Translations, speech segments, source documents and derived training views still overlap. Rows must not be summed into an independent-trace count. Shared institutional records appear under all attributed countries; country totals cannot be summed either. Missing country attribution on a serialized training view is not guessed from a joint policy parent.

The curated collection has 15 authored policy applications and 20 policy positions. The decision subset has 12 country views of two events, with seven attributed statements and five missing statements. No multi-agent trajectories or preference-pair dataset is prepared. The new applications are review candidates, not admitted training data. This does not erase the separate earlier China/Germany pilot runs.

## Annotated format and actual source records

1. **Blue / prompt:** system instruction, dated country/institution context, the question and supplied source evidence. These tokens condition the answer; the current trainer masks their supervised loss.
2. **Green / completion:** one assistant target answer, with `completion_only_loss=True`. The prompt and completion are a conversational dataset in the [TRL SFT format](https://huggingface.co/docs/trl/sft_trainer#expected-dataset-type-and-format).
3. **Ochre / review metadata:** provenance, admission state, source hashes/spans and split groups stay alongside the training record. Review fields are not appended as a model message. Evidence IDs and source context can already occur inside a prompt.
4. **Mode:** `chat_template_kwargs={"enable_thinking": false}` matches the repository’s [Qwen3-8B](https://huggingface.co/Qwen/Qwen3-8B) recipe. Preflight verifies the tokenizer’s prompt prefix and lengths before training.

For the four-country extension, the builder asserts equality against an existing on-disk SFT export. China/Germany prototype examples are converted from their actual `messages` and labeled as conversions, not existing admitted exports. The public JSON replaces source passages with an explicit omission marker; it is a redacted format preview, not a train-ready row. Authored claims and targets remain visible, with original publisher links. The private Space shows the full original prompt and completion. No source record or training file is changed by the presentation builder.

[RAFT](https://arxiv.org/abs/2403.10131) motivates supplying evidence during domain adaptation; this recipe is not a replication of its complete procedure. [PEFT LoRA](https://huggingface.co/docs/peft/conceptual_guides/lora) supplies the small-adapter implementation. [CheckList](https://aclanthology.org/2020.acl-main.442/) motivates behavioral tests: preserve supported differences and agreement, conditions, dates and attribution; do not count stylistic differences as persona success. DPO, continued pretraining and RL remain conditional future choices rather than implied available training datasets.

## Update without republishing source chunks

```bash
.venv/bin/python scripts/build_explorer_overview.py
.venv/bin/python -m pytest -q
node tests/explorer_overview_ui.cjs
```

This regenerates `explorer/overview.json`, the public/private static UI staging folders, and the GitHub country pages from the catalog plus the frozen candidate releases. Public output is explicitly projected; the full private format is never written into tracked overview files. Full static staging also invokes this builder. UI publication updates only `index.html`, `advanced.html`, `overview.js`, `overview.css`, and `overview.json`, preserving the existing source indexes, record buckets and archive.
