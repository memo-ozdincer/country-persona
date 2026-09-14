# Source explorer: counts, trace formats and contributions

The main interface is **Data explorer for persona fine-tuning**. Country buttons show counts immediately, followed by the record-type breakdown, source collections sorted by name, and worked post-training examples. Source sections expand to show task counts, measured field lengths, input/output mappings, available scoring evidence and an actual record reference.

The interface does not display personal authorship branding. Git history, citation metadata and original-publisher attribution remain intact.

## Count definitions

Country badges count distinct `record_id` values across source records, passages, observed actions, statistics and curated annotations. They exclude training-format copies, review/lineage objects, evaluation wrappers and profiles. Each record ID is assigned once per country, preferring its canonical version and using a stable UID tie-breaker. Source counts partition that selected set and sum to the badge.

The broader type breakdown preserves the earlier distinct-ID-per-type counts, including training and evaluation views. It overlaps across types and must not be summed. Translations and derived segments still have their own IDs: neither counting method estimates independent training trajectories. Country attribution follows the existing catalog; shared institutions and historical entities still need care.

Source-ID aliases are grouped in `explorer/source_profiles.json`. Project-curated claims and applications have their own collection with upstream evidence links. UN decision cases remain a small, explicitly labeled two-event collection. No new data or decision events are claimed by this interface change.

## Measured lengths

The inventory reads the original object through its catalog path/byte offset and verifies its content hash. For paired records it measures stored question/context/history fields joined with newlines and the target text separately. For existing authored `messages`, preceding messages and final assistant content are measured separately. For unpaired documents/passages it measures the text body.

The display reports median and nearest-rank p95 in **Unicode characters**, with the number of populated records (`n`). The JSON also contains minimum and maximum. These are not token estimates or full rendered training sequence lengths: country/date instructions and the model chat template can add input. Missing fields are not counted as zero-length examples. Whole-document length does not imply that the document is a target response.

## Record types and possible training uses

`explorer/trace_types.json` documents, for every actual source task:

- Which fields would be supplied as prompt/context at inference.
- Which answer, action, label or continuation would be generated.
- What supervision, scoring evidence or verifier is available or missing.
- Whether the mapping is an existing pair, a proposed conversion, or an incomplete task.

Authentic Q&A can support supervised answer adaptation. Vote and UPR-response labels can support classification and, after validating context and labels, potential offline verifiable tasks. Speech reconstruction needs correct speaker attribution and constructed prompting context. Monitoring-body reports must not be relabeled as the government’s own voice. Documents/statistics are evidence, not automatically complete tasks.

No interactive environments, multi-agent trajectories, implemented training reward verifiers or preference pairs are supplied in this snapshot. An exact-match vote score would not verify a rationale or recover private motives. A practical guide at the very bottom explains how to construct interactive environments, multi-agent trajectories, verifiers and preference pairs from suitable sources. It distinguishes proposed builds from existing records; the country view does not show a zero-count environment status strip.

Trace templates use explicit placeholders and link an actual record. They are not exported training rows. Public sample pointers include metadata/field names, not original source bodies. The full record remains available via the hosted catalog and publisher link.

The worked policy example uses existing evidence and a **clearly labeled question rewrite** for readability; original candidates are unchanged and remain unadmitted. China’s question now names the 2021 development-cooperation white paper and asks directly whether its stated policy permits political-system conditions on aid. It does not ask the reader to infer an unspecified hypothetical situation. The stored original candidate and redacted/full format remain inspectable.

## Research and library basis

[TRL conversational SFT](https://huggingface.co/docs/trl/sft_trainer#expected-dataset-type-and-format) supplies the prompt/completion representation. The existing trainer uses completion-only loss and the [Qwen3](https://huggingface.co/Qwen/Qwen3-8B) non-thinking chat template, with prompt-prefix/length verification. [PEFT LoRA](https://huggingface.co/docs/peft/conceptual_guides/lora) supplies the adapter mechanism.

[RAFT](https://arxiv.org/abs/2403.10131) motivates evidence-conditioned adaptation; the examples do not reproduce its full method. [CheckList](https://aclanthology.org/2020.acl-main.442/) motivates tests of supported policy differences, agreement, conditions and attribution. No paper makes these source records automatically valid environments; task construction and evaluation remain empirical work.

## Living repository workflow

The public overview runs from committed static files. Contributors can edit source descriptions, trace recipes and the interface without Trillium access; see [CONTRIBUTING.md](../CONTRIBUTING.md). Source proposals and corrections have GitHub issue templates.

```bash
python3 -m http.server 8000 --directory explorer
python3 scripts/validate_source_inventory.py
node tests/explorer_overview_ui.cjs
```

Maintainers with the frozen data can regenerate the inventory and stage both existing Spaces:

```bash
.venv/bin/python scripts/build_explorer_overview.py
.venv/bin/python -m pytest -q
.venv/bin/python scripts/publish_explorer_ui.py --publish
```

Publishing uses the existing owner login and preserves public/private visibility. It updates only UI, metadata and documentation assets; the original record buckets and archive are unchanged. Cluster synchronization is not required to work on this public explorer.
