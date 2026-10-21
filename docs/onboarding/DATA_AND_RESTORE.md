# Data and checkpoint access

[Start here](README.md) · [Environments](ENVIRONMENTS.md) · [Pinned release/asset manifest](artifacts.json)

## What a collaborator gets

| Material | Where it is | Plain clone sufficient? |
|---|---|---|
| Code, configs, trial descriptions, evaluation guide and generated-answer pages | Git `master` | Yes |
| Eight-example short-answer data, all 94 stored answers, original logs/configs/reviews | Embedded as 130 exact text files in the tracked offline HTML | Yes; use `verify_starter.py --extract` to get normal files |
| Meeting-context data and most recent bounded source/writer evidence | Tracked `research/` and `reports/` | Yes for those tracked files; dependencies on older sources may require v47 |
| Earlier selected sources, frozen evaluation data, full historical run artifacts and older LoRA adapters | Private `snapshot-v47` release | No; restore the pinned snapshot |
| Trial 4 authentic-speech adapter/run archive | Private `meeting-context` release | No |
| Trials 5, 6, 7 adapters | Private `source-writer`, `application-writer`, `scope-writer` releases | No |
| Base model weights, credentials, installed environments and caches | Separate Hugging Face download / collaborator-owned credentials and environment | Deliberately external |
| Large older/Reddit corpora and some historical redundant/partial exports | Not fully included in this handoff | No blanket availability claim; see the source inventory after restore |

The immutable v47 snapshot contains **14,958 files / 6,140,263,018 bytes**. Its compressed delivery is **3,641,228,051 bytes**, divided into four parts, plus a multipart manifest and receipt. Current code and later bounded evidence are a committed Git overlay. A current clone plus the restored snapshot and later adapter releases reproduces the selected archived research boundary; it does not recreate every older bulk collection.

On 21 October, live GitHub metadata for **18 assets across five private releases** matched the pinned sizes and SHA-256 digests. [Exact names, release links and hashes](artifacts.json). This is metadata verification, not a new multi-GB download or a test of every collaborator's permissions.

## Start small: no release download needed

```bash
python3 -B docs/onboarding/verify_starter.py
python3 -B docs/onboarding/verify_starter.py --extract /absolute/scratch/path/new-starter-evidence
```

The extracted text preserves the exact original relative paths and bytes. Adapter binaries and original PDFs are not part of this bounded extraction. The full original replay script requires additional original sources/adapters; the onboarding check intentionally verifies the clone-accessible byte bindings and score arithmetic instead.

## Full historical evidence restore

Use separate fresh scratch paths for downloads, extracted snapshot, and current clone. Never extract into the authoritative Aurora evidence tree or overwrite an existing research workspace.

1. Open the private [snapshot-v47 release](https://github.com/memo-ozdincer/country-persona/releases/tag/aurora-handoff-20261007-v47). Download all six assets named under `snapshot-v47` in [artifacts.json](artifacts.json): four ordered parts, the multipart JSON and the receipt. Use authenticated GitHub access; do not place a token in a URL or command argument.
2. Verify the downloaded files and assemble a fresh whole archive:

```bash
python3 -B docs/onboarding/verify_downloads.py --release snapshot-v47 \
  --directory /absolute/scratch/downloads/v47 \
  --assemble /absolute/scratch/restore/v47.tar.gz
```

The parent of the assembly filename must already exist. The helper checks each asset, uses the pinned part order from [v47-multipart.json](v47-multipart.json), and checks the combined archive size/hash. It never overwrites, extracts, deletes or downloads anything.

3. Extract into a new empty directory, then verify the unmodified snapshot:

```bash
mkdir /absolute/scratch/restore/v47
tar --extract --gzip --file /absolute/scratch/restore/v47.tar.gz \
  --directory /absolute/scratch/restore/v47 --no-same-owner

python3 -B /absolute/path/to/current-clone/scripts/verify_research_handoff.py \
  --root /absolute/scratch/restore/v47
```

Expected snapshot manifest SHA-256: `fafbe6a52c944fe7ceb9abc473b7f7924566c1260d8d925691aedf20a915ea9b`. Expected base commit: `97f0f3bbbdce291eb6444d0d82d1c0c53d1c6644`. Do not regenerate a manifest to excuse a mismatch.

4. In a **fresh current Git clone**, fill missing payload files from the verified extracted snapshot while keeping current tracked files. With rsync installed:

```bash
rsync -a --ignore-existing /absolute/scratch/restore/v47/ /absolute/path/to/current-clone/

python3 -B /absolute/path/to/current-clone/scripts/verify_workspace_overlay.py \
  --root /absolute/path/to/current-clone \
  --manifest-sha256 fafbe6a52c944fe7ceb9abc473b7f7924566c1260d8d925691aedf20a915ea9b
```

Run this before installing or building the project there. The verifier requires a clean Git checkout and checks unchanged ignored evidence plus the current committed files. The unmodified-snapshot verifier will intentionally fail on overlaid code/documentation; that does not justify changing its hashes.

Keep the immutable extracted snapshot separate. If you later remove a redundant whole archive, follow [the storage policy](../STORAGE_POLICY.md): verify parts/reassembly and remote assets, record a cleanup receipt, and retain a recoverable delivery representation. This onboarding task creates no replacement multi-GB archive.

## Later adapters: download only what the chosen trial needs

| Onboarding name | Release key | Restore details |
|---|---|---|
| SFT Trial 4 | `meeting-context` | [Bounded archive and member manifest](../../reports/scenario-checkpoint-delivery-20261018-v1.json) |
| SFT Trial 5 / historical native32 | `source-writer` | [Adapter manifest and metadata-copy instructions](../../reports/native-plan-writer-adapter-manifest-20261019-v1.json) |
| SFT Trial 6 / historical native40 | `application-writer` | [Adapter manifest and metadata-copy instructions](../../reports/native-application-writer-adapter-manifest-20261019-v1.json) |
| SFT Trial 7 / historical native48 | `scope-writer` | [Adapter manifest, metadata pairs and dependencies](../../reports/native-scope-partial-adapter-manifest-20261019-v1.json) |

Download that release's listed assets into a fresh directory, then run:

```bash
python3 -B docs/onboarding/verify_downloads.py --release application-writer \
  --directory /absolute/scratch/downloads/trial-6
```

Follow the chosen adapter manifest to copy tracked metadata mirrors into fresh historical run destinations and place the verified adapter/config there. Historical scripts can depend on exact original baseline paths, source PDFs and other archived files; copying one adapter does not by itself reproduce a run.

## Limits a new collaborator should know

The snapshot manifest explicitly excludes credentials, base weights, virtual environments/caches and large older bulk corpora. `handoff/source-inventory.json` records coverage of the selected roots after restore; it includes six partial/omitted rows, including redundant exports and some historical preparation artifacts. These omissions are preserved rather than silently filled. Ask which exact artifact is required before attempting a historical rebuild.

Germany/China work and historical releases are preserved. Public source availability is not a blanket redistribution license. New collaborators need private repository/release access separately from cluster/model access. The [onboarding validation receipt](CHECKS.md) states what was actually tested and what remains untested.
