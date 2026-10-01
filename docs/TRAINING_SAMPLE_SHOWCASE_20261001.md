# Shareable training samples — 1 October 2026

Open [the offline sample viewer](../explorer/training-samples.html) in a browser. It shows short previews and expandable full records for the original UN statements, assistant-processed bullet plans, exact SFT input/target and saved base/adapter answers. No server or model runtime is needed.

For forwarding, send the single HTML file, or [the 1.5 MB ZIP](../runs/training-sample-showcase-20261001-v2/training-samples.zip). The ZIP includes the viewer, three original meeting PDFs, exact raw JSON/JSONL and source-hash receipt. The [exact training JSONL](../runs/training-sample-showcase-20261001-v2/training-points.jsonl) is also available separately.

Both actual points from the latest complete-task fit are included: climate/security and Ukraine. South Sudan is labeled as an outside-training comparison, already exposed in development; it has no training target in this release. The six historical model answers are unedited. The two training-context comparisons are controls, not held-out results.

The session assistant read the complete bounded national statements and authored the checked plans and synthetic analyst-memo targets after inspecting earlier errors. There was no separate teacher API run or standalone teacher conversation transcript. The viewer preserves the saved source packet, specifications and outputs rather than inventing that transcript. The student receives the checked plan as input; SFT loss covers the assistant's full memo completion only. This teaches realization of supplied positions; it does not demonstrate national decision prediction or persona improvement. Independent semantic review remains pending.

[Export and browser verification receipt](../reports/training-sample-showcase-20261001.json) binds the files and checks. Frozen source manifests, text digests, quote locations, PDF hashes, target equality and before/after input-token identity pass. The browser displays all source, plan, target and output texts exactly, switches all three cases, expands/collapses full records, and downloads the original training file byte-for-byte. Desktop and mobile layouts have no horizontal overflow or JavaScript errors. A v1 page-label error was corrected in v2; the earlier export and browser launch failures remain preserved.

Zero new model calls, optimizer steps or GPU launches. The dedicated CPU browser session was closed after checking its recorded identity; unfamiliar processes were untouched. The research diagnosis and latest measured checkpoint remain unchanged.

To rebuild from the frozen artifacts, choose a fresh output directory:

```bash
python3 scripts/build_training_sample_showcase.py \
  --output runs/training-sample-showcase-FRESH
```

This writes a new portable folder and sibling ZIP, and refreshes the generated viewer from [the template](../explorer/training-samples.template.html). Source packs and historical transcripts stay unchanged. The current verified export is `runs/training-sample-showcase-20261001-v2/`; a copy of its ZIP sits inside that directory so the research handoff includes it.
