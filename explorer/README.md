# Country Persona Explorer

The default page is the simple country overview; the full catalog is `advanced.html`. Rebuild UI assets and representative examples with `python scripts/build_explorer_overview.py`. See `docs/EXPLORER_PRESENTATION.md` for exact field mappings, redaction and count semantics.

Created and maintained by **Memo Ozdincer**.

Static hosted explorer plus a read-only local Python/SQLite explorer with a public metadata mode and an explicitly enabled full research mode. No Python server dependencies outside the standard library. Build dependencies are in `scripts/build_data_catalog.py` (PyArrow); they are not needed to serve an already built snapshot.

See [the exploration guide](../docs/DATA_EXPLORER.md) for links, counts, limitations and update commands. Public and private deploys use the same app; only the private deploy contains the source archive. Never copy credentials into a Space directory or enable private source access in the public deployment.

Hosted Spaces use `data-client.js` and type-specific compressed indexes. The local Python server remains useful for direct source-file downloads. Static private hosting supplies record bodies on demand and links to a separate private dataset containing the original-file archive.
