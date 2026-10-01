# Data explorer for persona fine-tuning

Country counts, source inventories, trace schemas and possible training uses.

For a shareable training-data walkthrough, open [training-samples.html](training-samples.html) directly in a browser. This standalone file works offline and shows both actual complete-memo training points, full original statements, checked bullet plans, exact SFT rows and saved model outputs. Short previews expand to complete records. The [sample guide](../docs/TRAINING_SAMPLE_SHOWCASE_20261001.md) links the companion ZIP with original PDFs and raw files, provenance and verification receipt.

For local preview, run `python3 -m http.server 8000 --directory explorer` from the repository root. The main view uses committed JSON; the full advanced catalog also needs its larger staged indexes or the local API server.

See [CONTRIBUTING.md](../CONTRIBUTING.md) for source proposals and validation. Source metadata and trace recipes can be edited without cluster access.
