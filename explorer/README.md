# Country Persona research website

[index.html](index.html) is the illustrated research homepage: project goals, corpus graphics, evaluation design, preliminary comparisons, and the proposed post-training loop. Interactive figures use [homepage-data.json](homepage-data.json), rebuilt from stored inventories and measured receipts with `python3 scripts/build_research_homepage.py` from the repository root.

The original country/source explorer is preserved at [data.html](data.html). Legacy `index.html#country=...` links continue there automatically.

Country counts, source inventories, trace schemas and possible training uses remain available in the data explorer.

For a shareable training-data walkthrough, open [training-samples.html](training-samples.html) directly in a browser. This standalone file works offline and shows both actual complete-memo training points, full original statements, checked bullet plans, exact SFT rows and saved model outputs. Short previews expand to complete records. The [sample guide](../docs/TRAINING_SAMPLE_SHOWCASE_20261001.md) links the companion ZIP with original PDFs and raw files, provenance and verification receipt.

For local preview, run `python3 -m http.server 8000 --directory explorer` from the repository root. The main view uses committed JSON; the full advanced catalog also needs its larger staged indexes or the local API server.

See [CONTRIBUTING.md](../CONTRIBUTING.md) for source proposals and validation. Source metadata and trace recipes can be edited without cluster access.

The homepage uses a numbered research-brief format. It lists country flags, exact inventory counts, stored record examples, evaluation criteria, preliminary findings, and method status. `catalog-summary.json` preserves the public catalog snapshot. `homepage-data.json` includes exact examples and input hashes. See [the revision receipt](../docs/RESEARCH_HOMEPAGE_REVISION_20261005.md).

The current presentation uses a plain white document layout with conventional Times-style type and common blue/gray figures. The page preserves its headings, records, counts, and measured values. Website chrome and the source-file volume display are removed. See [the style receipt](../docs/RESEARCH_DOCUMENT_STYLE_20261005.md).

Section heading sizes and spacing distinguish the eight sections. Two thin rules mark evaluation and post-training methods. Four document tables use light gray cell and outer borders. The text, figures, examples, and data remain unchanged in this refinement.

The document opens with its title and author. Project-series, month, summary-subtitle, and preliminary-status labels are removed. See the final cleanup and identity checks in [the style receipt](../docs/RESEARCH_DOCUMENT_STYLE_20261005.md).
