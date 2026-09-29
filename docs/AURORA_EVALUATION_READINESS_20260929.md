# Aurora evaluation portability and readiness — 29 September 2026

**The frozen evaluation reproduces on Aurora, and all nine synthesis prompts retain their original tokenization. No Aurora model inference or training ran.** This checkpoint asks whether the transferred evidence can support the next bounded development comparison. It does not add independent ratings or model-quality results.

## Evidence inspected

- Before editing, all **9,046 files / 500,998,395 bytes** verified against the original transfer manifest, SHA-256 `ecfb8199bca71839bfbda87ea4d778c880c125ee3a1556d612e6f55affcc6da4`. The tracked working diff also exactly matched the transferred patch.
- A fresh replay of all 42 provisional assistant reviews produced **byte-identical scores**: 516 dependent rating instances, comprising 366 met, 117 unmet and 33 unratable. Both country-macro peer gains remain null. Independent construct and semantic review remain pending.
- The original **63 focused software tests passed again**.
- A fresh tokenizer-only preflight using Transformers 4.57.6 and Jinja2 3.1.6 matched all nine original input-token digests, pack/model-lock hashes and EOS settings. Total input: **37,823 tokens**; maximum: **5,669**. With the common 2,048-token output allowance, the maximum is **7,717 / 8,192**. No source or prior note was truncated.

These observations support portability of existing arithmetic and prompts. Exact quotation matching still does not certify entailment, and software checks do not validate the proposed semantic rubric.

## Broader software checks and their limits

Broader checks exposed an HTML encoding dependency: valid UTF-8 typographic apostrophes could be misdecoded before the spokesperson parser ran. The parser now tries UTF-8 first and retains declared-encoding fallback for other bytes. Existing MFA tests and one additional Windows-1252 regression check pass. No Germany/China release was regenerated or relabelled.

With the required optional data packages available, the final broad run produced **166 passed, 2 failed and 6 skipped**. The two failures require intentionally omitted material: the original prepared `country-knowledge-20260914/source-text/es11_pv5.txt`, and public/private explorer example caches. Available raw text variants do not have the prepared file's required hash; they were not substituted. Four workshop tests skip for omitted source preparation; inference and training-check modules skip because PyTorch is absent. Earlier dependency/encoding failure logs are retained. This is not a claim that the full suite passed.

## Execution readiness and next decision

The live host is `aurora`. At this checkpoint GPUs 1, 2, 3, 4, 5 and 7 reported zero memory use; GPUs 0 and 6 held existing processes. This is an occupancy observation, not a reservation. No existing process or allocation was changed.

The scratch Hugging Face cache contains no locked Qwen3-8B weight snapshot, and no verified Aurora PyTorch/CUDA inference environment exists yet. Only temporary CPU test/tokenizer environments were used, with caches redirected by the private Aurora profile. Their actual package and Python versions are recorded separately; they are not a production runtime comparison.

**Next:** prepare and verify the exact locked model bytes and a scoped Aurora inference runtime, then recheck GPU occupancy and record a single-device launch for the nine-call format diagnostic. Inspect every delivered answer against its sources before choosing another experiment. Independent evaluation review and Aurora CUDA/NCCL training remain pending; the older Germany/China adapter regression remains part of the history.

## Artifacts and synchronization

- [Checkpoint receipt](../reports/aurora-evaluation-readiness-20260929-v1.json)
- [Fresh review scores](../runs/aurora-evaluation-replay-20260929-v2/scores.json), [review receipt](../runs/aurora-evaluation-replay-20260929-v2/receipt.json), and logs in that run directory
- [Fresh format preflight](../runs/aurora-format-preflight-20260929-v1/preflight.json) and [tokenizer environment](../runs/aurora-format-preflight-20260929-v1/environment.json)

The private GitHub synchronization captures the formerly uncommitted code, documents and reports. Ignored frozen data, reviews, transcripts and source files require the separate [private handoff archive](https://github.com/memo-ozdincer/country-persona/releases/tag/aurora-handoff-20260929-v2); a code clone alone still does not reproduce this workspace. The refreshed snapshot is generated and verified separately, with original transfer metadata preserved. Model weights and credentials remain excluded.
