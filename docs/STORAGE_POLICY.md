# Storage and synchronization policy — 14 October 2026

Preserve unique research evidence, model adapters, historical branches/releases and Germany/China work. File size alone is not a deletion criterion. Credentials and base weights stay outside the repository and private handoff; bulky files remain under project scratch.

## Two durable layers

1. **Immutable research snapshot:** v47, base commit `97f0f3bbbdce291eb6444d0d82d1c0c53d1c6644`, 14,958 payload files / 6,140,263,018 bytes. Its manifest SHA256 is `fafbe6a52c944fe7ceb9abc473b7f7924566c1260d8d925691aedf20a915ea9b`. The existing private release retains four ordered parts, multipart manifest and receipt.
2. **Committed Git overlay:** subsequent code/documentation/audit reports. Code-only changes do not require repackaging the entire research snapshot. Push both the research branch and master without forcing; check remote state first. Keep ignored research payloads unchanged in this mode.

After committing, run the pinned overlay verifier shown in `START_HERE.md`. It requires a clean checkout, checks snapshot ancestry, hashes unchanged payloads and verifies every tracked working file against its committed blob. Only files already tracked in the snapshot's base commit may replace snapshot content through this overlay. Changed or newly produced ignored evidence requires a reviewed artifact backup/new full snapshot; this verifier does not inventory arbitrary extra ignored files. A full clean snapshot restore still uses `verify_research_handoff.py`.

Do not rewrite the original manifest to bless a mismatch. Do not report a live overlaid checkout as byte-identical to the original snapshot. `CURRENT_HANDOFF.json` must distinguish snapshot base commit from workspace commit and record the overlay verification receipt.

## Delivery archives and retention

Retain one necessary local delivery representation: either the whole archive or its complete ordered parts. Keeping both indefinitely duplicates every compressed byte. Before removing a redundant whole copy, verify each part, the ordered combined hash, the whole archive hash, the frozen receipt and remote asset sizes/digests. Record exact path/hash/identity, preserved restore paths and completed removal in a cleanup receipt. Reconstruct only into a fresh file and check the whole digest before extraction. Do not infer ordered parts from a filename glob.

On October 14 the verified redundant v47 whole archive was removed, reclaiming 3,641,228,051 logical bytes. Four local parts, immutable staging tree, original receipts and all remote assets remain. Historical documents describing a locally retained whole v47 archive record the earlier state; the current external metadata/cleanup receipt records this intentional change. The uploader requires a reconstructed whole archive if that old release is ever uploaded again.

For example, with Python's standard library, read `parts` from `aurora-explicit-seed-preparation-20261007-v47-multipart.json`, open a fresh destination with mode `xb`, and stream each named local part into it in list order. Verify its size is 3,641,228,051 and SHA256 is `812de7c7e8636c2a4a900020eb9fd9397f38d041b494423a20bf98951cce2dd5` before using it. No redownload is needed while the verified local parts remain.

Older delivery duplicates remain candidates for the same verified compaction, not an automatic purge. Do not delete immutable snapshot directories, releases, datasets, model caches or environments to satisfy an arbitrary size target. Extracted package documentation links and cache lock files are not evidence of dataset corruption. Never delete a lock based only on its age or zero length.

## Hardlinks, metadata and I/O

Build/install the project in a disposable Git-only checkout, with environments and caches on scratch. An editable install in the authoritative evidence checkout regenerates `src/country_persona.egg-info`, which is part of the frozen payload. Preserve that historical metadata; do not update its snapshot hashes to match a new build. See the [19 October CI repair and exact restoration](CI_REPAIR_20261019.md).

Historical stages share hardlinked files. Treat them as immutable; detach any linked workspace file before editing it. Count unique inodes when measuring allocation, and distinguish apparent bytes from allocated bytes. Cached runtime files already share hardlinks; deleting their names may reclaim very little.

Avoid repeatedly walking every historical stage or hashing all historical archives for routine code edits. Inventory old stages from their manifests and fully verify the current recovery boundary. State the scope: this is application-level byte integrity, not certification of MFS replication, disks or cluster-wide health. Keep a concise current-state summary and link dated evidence instead of duplicating the entire chronology into every entry document.
