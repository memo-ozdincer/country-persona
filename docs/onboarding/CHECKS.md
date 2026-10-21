# What was actually checked

[Start here](README.md) · [Machine-readable receipt](onboarding-checks.json)

Verified 21 October 2026, America/Toronto. This was an onboarding/data/environment audit, not a new model-quality experiment. The research goal remains paused.

| Check | Outcome | Practical meaning |
|---|---|---|
| Fresh private GitHub clone | Created from `master` at `5e701ffb0a23ec280140404bdff6481f176e3972` | The check did not borrow ignored research data from the authoritative workspace. Candidate onboarding helpers were copied separately and byte-verified. |
| New CPU environment | Built successfully with the new helper and locked profile | Python 3.11.13, CPU PyTorch 2.8.0+cpu and the measured six research-library versions; no editable project installation. |
| Full CPU test suite in that clone | **242 passed, 23 skipped, zero failures/errors** | The skips explicitly depend on unavailable private artifacts. This is software validation, not persona quality. |
| Source inventory and code compilation | Passed | Documentation inventory references and Python syntax compile in the clone. |
| Clone-only evidence replay/extraction | Passed | 130 embedded text files verified and extracted; 94 original answer/review bindings and 23/40 → 34/40 → 38/40 arithmetic reproduce. |
| Private GitHub release metadata | **18 assets across five release sets verified** | Live sizes/SHA-256 digests match the pinned receipts. No multi-GB archive redownload was needed. |
| Existing GPU environment | All 75 package dependencies compatible; six key version/build pins match | Existing measured Python 3.12.3 / CUDA 12.8 environment is documented. No CUDA allocation, model loading or fresh GPU rebuild occurred. |
| Download verification helper | Six small integrity checks pass | Accepts valid bytes, rejects size/hash corruption, assembles explicit part order, refuses overwrite and preserves a failed combined-hash output for inspection. The full v47 archive was not reassembled again. |

The first isolated helper-copy attempt resolved its source path incorrectly and created empty candidate files; no installation/tests ran in that attempt. It was corrected using the absolute authoritative source and byte checks before the real setup/test run. The failure receipt is preserved in the external audit directory. No original data, model outputs or snapshot manifest was changed to hide it.

The historical hosted CI also passed [242 tests with 23 explicit private-artifact skips](https://github.com/memo-ozdincer/country-persona/actions/runs/39337006149). The new local check validates the documented dependency-only setup in a fresh clone, without relying on a package editable install.

## Still separate or unproved

- A plain clone is not the complete frozen research workspace. Restore v47 and the chosen later checkpoint as described in [the data guide](DATA_AND_RESTORE.md).
- Base weights and credentials are external. A collaborator's repository/release/cluster/model access must be granted separately; this audit cannot certify another person's permissions.
- The GPU recipe is captured and the existing environment checked; a clean GPU rebuild and new CUDA run were not performed for onboarding. Historical measured runs remain the GPU evidence.
- Archive asset metadata and pinned local evidence do not certify the MFS hardware or guarantee future source-host availability.
- Semantic grading is still mostly by the same assistant that curated the examples. Independent source/rubric review and strong OOD/persona/multi-agent gains remain open.

All detailed logs, the fresh clone/environment and the preparation-error receipt are retained under `/mfs1/u/memo/country-persona-research/audits/onboarding-20261021-v1/`. The JSON receipt records their hashes and the exact helper bytes tested. No new production generation or optimizer update is attributed to this task.
