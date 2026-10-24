# Download the research directly from Hugging Face

[Onboarding](README.md) · [SFT Trials 1–7](SFT_TRIALS.md) · [Full data/restore guide](DATA_AND_RESTORE.md)

**Private dataset: [memo-ozdincer/country-persona-aurora-data](https://huggingface.co/datasets/memo-ozdincer/country-persona-aurora-data).** Sign in with an account authorized to access it. Aurora access is not required to browse or download the files.

The export contains **15,826 files / 6,442,905,503 bytes (6.44 GB)**. Its `workspace/` directory preserves the research's original relative paths: source material, prepared training/evaluation data, complete generated outputs, reviews, code/configuration, onboarding/environment definitions, and saved LoRA adapters.

## Browse

| Material | Direct folder/page |
|---|---|
| Training/evaluation packs | [workspace/data/prepared](https://huggingface.co/datasets/memo-ozdincer/country-persona-aurora-data/tree/aurora-20261024-v1/workspace/data/prepared) |
| Raw source material | [workspace/data/raw](https://huggingface.co/datasets/memo-ozdincer/country-persona-aurora-data/tree/aurora-20261024-v1/workspace/data/raw) |
| Full model outputs and historical adapters | [workspace/runs](https://huggingface.co/datasets/memo-ozdincer/country-persona-aurora-data/tree/aurora-20261024-v1/workspace/runs) |
| Later source/writer experiment packs | [workspace/research](https://huggingface.co/datasets/memo-ozdincer/country-persona-aurora-data/tree/aurora-20261024-v1/workspace/research) |
| Every file, size and SHA-256 | [FILE_MANIFEST.json](https://huggingface.co/datasets/memo-ozdincer/country-persona-aurora-data/blob/aurora-20261024-v1/FILE_MANIFEST.json) |

You can open a file and use its download button. The earlier GitHub release archives remain available as an alternative recovery representation; downloading this dataset does not require reassembling those archives.

## Download everything

Use the Hugging Face Hub client in your own download environment (`python -m pip install "huggingface_hub==1.33.0"` if needed). Authenticate with your own authorized account using `hf auth login`; never put a token value in a command argument or commit it. On Aurora, choose a destination under your own scratch directory, not CSlab home.

```python
from huggingface_hub import snapshot_download

snapshot_download(
    repo_id="memo-ozdincer/country-persona-aurora-data",
    repo_type="dataset",
    revision="aurora-20261024-v1",
    local_dir="country-persona-aurora-data",
    token=True,
)
```

Verify the full downloaded payload:

```bash
python3 -B country-persona-aurora-data/VERIFY_DOWNLOAD.py
```

The verifier uses only Python's standard library. It checks the pinned manifest and each selected file's size and SHA-256. This checks bytes, not independent model-quality judgments.

## Download only SFT Trial 2's eight-example pack

The complete pack is seven files / 167,135 bytes. Download it with the manifest and verifier:

```python
from huggingface_hub import snapshot_download

snapshot_download(
    repo_id="memo-ozdincer/country-persona-aurora-data",
    repo_type="dataset",
    revision="aurora-20261024-v1",
    local_dir="persona-trial-2",
    token=True,
    allow_patterns=[
        "workspace/data/prepared/minimal-country-20261005-v2/**",
        "FILE_MANIFEST.json",
        "VERIFY_DOWNLOAD.py",
    ],
)
```

```bash
python3 -B persona-trial-2/VERIFY_DOWNLOAD.py \
  --prefix workspace/data/prepared/minimal-country-20261005-v2/
```

The source models' base weights, installed environments, caches and credentials are not included. Adapter weights are included. Historical configs retain their original absolute paths; adapt a copied run-specific config before any future model execution, as explained in [the environment guide](ENVIRONMENTS.md).

## Exact scope and provenance

The payload combines the pinned v47 frozen evidence, Git source commit `6c6f5cfa2331b299dcf789e788f905586f046a9e`, and the separately verified later runtime/adapters. No original snapshot manifest was rewritten. The dataset root's `STATUS.json` and the publication receipt record the remote content verification and pinned Hub revision.

The snapshot omits some larger older/Reddit corpora; this export does not silently invent or recover them. Earlier workshop/Reddit files remain in the separate [private research-files dataset](https://huggingface.co/datasets/memo-ozdincer/country-persona-research-files). Population/community behavior and institutional government behavior remain different targets.

The dataset and existing GitHub releases stay private. No collaborator permissions were changed. The 24 October publication adds no model calls or optimizer updates; research remains paused. The latest onboarding text remains in GitHub, while `workspace/` is a pinned copy of the stated research boundary.
