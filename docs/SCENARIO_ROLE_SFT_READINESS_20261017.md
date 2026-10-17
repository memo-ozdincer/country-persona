# Scenario/delegation SFT: source-audited setup — 17 October 2026

The data, response-only training loop, evaluation harness and inspectable validation artifacts are implemented. **No new production-model answers or updates, GPU allocations or persona-quality results.** The final CPU proof uses a random tiny Qwen3.5; actual 4B execution remains pending. Cumulative production Qwen3.5 stays 3,934 updates, separate Qwen2.5 reference 582. Earlier experiments and the unrun explicit seed-only control remain unchanged.

## Frozen data and grounding

The bounded Git-tracked release is [research/scenario-role-sft-20261017-v1](../research/scenario-role-sft-20261017-v1/README.md). It contains four complete authentic national speeches: India and the UK in sanctions S/PV.9214 and climate S/PV.8923. Two complete India/UK speeches from Ukraine S/PV.9138 are excluded from this fit. These records have historical project exposure and possible pretraining exposure; Ukraine is development transfer, **not sealed OOD**. France has no national speech in the selected sanctions record; none is invented.

The same root assistant hand-read all six targets, all selected prior context, the complete short sanctions record, scenario/header metadata and the rendered boundaries. For the two longer records, unused speeches were not all hand-read. Official PDF covers and target/context boundaries were visually checked: sanctions pages 1/3/4/7/8; climate 1/17–21/23/24; Ukraine 1/8–10. The new extraction recovers printed hard hyphens lost by the old extractor. Across 54 body pages, column word inventories equal the body crop and full-width body inventory. All 54 excluded top/bottom text regions were read: only headers/footers, no speech body. This is extraction coverage, not independent semantic certification.

Every supplied documentary body character is mapped to a source span, page/column and digest. All scenario evidence anchors precede the target. Serialization markers, task instructions and institutional labels are identified as authored metadata. India's chair announcement, national speech and chair resumption are separate; resumption is excluded from the target. The earlier sanctions vote is legitimate reconstruction context and rules out forecasting claims.

Normalization is reversible: whitespace within columns, two discretionary soft hyphens and 34 printed-hyphen line wraps, with raw coordinates and exact before/after text. Printed grammatical irregularities remain unchanged. Sources, raw column text, normalization ledger and official PDF pins are retained; the original ignored sources are untouched. Re-extraction reproduces all seven source files exactly; rebuilding reproduces all eleven pack files exactly. The builder's release status records its construction boundary; later hand review and runtime readiness are recorded separately in `quality-review.json` and `validation/`.

Full earlier history fits for sanctions. For climate/Ukraine, even unlabelled full past exceeds the fixed 6,144-token prompt allowance. The declared fallback keeps the immediately preceding **complete** speech, never a target-selected snippet, with no inferred summary of omitted turns. Every example leaves 2,048 generation tokens within 8,192. The India climate target is 1,744 supervised tokens, so the cap permits a complete reproduction. Authentic targets remain unequal in length; the objective weights examples equally and records token exposure separately.

| Case | Split | Masked prefix | Supervised speech + EOS |
|---|---|---:|---:|
| Sanctions UK | fit | 2,042 | 260 |
| Sanctions India | fit | 5,801 | 574 |
| Climate India | fit | 1,764 | 1,744 |
| Climate UK | fit | 1,121 | 570 |
| Ukraine India | development | 669 | 301 |
| Ukraine UK | development | 778 | 505 |

Grounding here means faithful attribution to a pinned public record. It does not independently establish the truth of every diplomatic, legal or scientific assertion, recover private motives, or verify later corrections to these provisional English records. Independent semantic review remains pending.

## Harness and loop

[The generic module](../src/country_persona/scenario_sft.py) and [single-operation runner](../scripts/run_scenario_sft.py) implement:

- Exact source rendering, tokenizer/file locks, no future turns, no silent truncation or sequence packing; context/header labels are `-100`, complete speech plus existing `<|im_end|>` supervised. First target is predicted at the last prefix position. Target-only vocabulary logits match the full causal loss.
- Fresh rank-8/alpha-16 LoRA over all linear modules, zero initial output effect, BF16/SDPA, nonreentrant checkpointing, AdamW at 5e-5 without weight decay, clipping 1, batch/accumulation 1. No added tokens, resized embeddings or old adapter continuation in this first arm.
- Four targets × 32 presentations = 128 planned updates; seeded per-epoch shuffle. Planned exposure is 444,032 sequence tokens and 100,736 supervised tokens. These are planned exposures, not actual production updates or unique examples.
- Every optimizer step records actual input/mask hashes, tokens, loss, gradient norm and case identity. Replay rejects altered masks, order, counts and nonfinite values. Frozen-base tensor versions, actual adapter changes and safe save/reload are checked; failures preserve partial traces.
- Generation receives the prompt only. Complete output token IDs, raw special tokens, display text and cap status are retained. Per-case speech NLL and a wrong-requested-country/representative NLL diagnostic preserve the same actual past. An ordinary-chat base control supplies the same scene/history with explicit continuation instructions. That is a practical strong baseline, not an isolated serializer ablation.
- Twenty-eight frozen material criteria with complete source support and four whole-answer guards. A semantic reviewer must read each complete raw response, cite actual answer quotes and mark uncertainty explicitly. Blank/stale reviews or unquoted “met” grades fail validation. Loss/NLL does not auto-award a persona grade.

The final random tiny **hybrid** Qwen3.5 CPU proof runs the same loss/optimizer/save code for eight steps. All eight traces were inspected and replayed. Both attention types execute; gradients are finite, adapter tensors change, frozen base versions remain unchanged, and a separate fresh base reload reproduces adapter tensors and logits exactly. The causal first-token/EOS tests and generation spy pass. **32 focused pytest checks + 3 pinned-runtime unittest checks = 35 passing software checks.** Reference PyTorch linear-attention/causal-convolution fallbacks are present; GPU throughput/memory are unmeasured for this loop. No NCCL claim.

Two early preparation errors were corrected before any production execution: the raw-history allowance initially omitted the generation reserve; relative source paths initially failed release writing. The partial pack is preserved externally and the final pack was rebuilt byte-identically. See [the readiness receipt](../reports/scenario-sft-readiness-20261017-v1.json).

## Next concrete checkpoint

Run and inspect the two sequence-format base Ukraine answers on a freshly checked free **NVIDIA RTX PRO 6000 Blackwell Server Edition**. The runner requires zero memory/utilisation/no resident process, verifies pinned weights and records process identity; it never waits for a device, touches unfamiliar processes or launches a queue. Use the ordinary-chat base control before interpreting a serializer failure as missing capability.

Inspect both complete base outputs with the frozen rubric and record a source-bound decision. If fitting is informative, the runner accepts that inspected base run and performs only the frozen four-example fit. Then inspect fitting reproduction and the same two Ukraine inputs under the saved adapter. Replan on source/role errors; exact fitting recall alone does not justify scaling. The atomic-token arm remains deferred until an inspected readable-marker result warrants it. This setup request does not automatically launch those production steps.
