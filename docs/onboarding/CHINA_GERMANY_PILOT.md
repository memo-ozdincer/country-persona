# China/Germany original pilot: canonical records and SFT candidates

[Onboarding](README.md) · [All data downloads](PRIVATE_HF_DATA.md)

The original China/Germany pilot was added to the public [Hugging Face dataset](https://huggingface.co/datasets/memo-ozdincer/country-persona-aurora-data) on 29 October 2026. No account or Aurora access is needed. This repairs an omission from the original Aurora-only upload.

| Material | Exact count | Open |
|---|---:|---|
| China candidate conversations | 12,471 | [CHN](https://huggingface.co/datasets/memo-ozdincer/country-persona-aurora-data/tree/aurora-20261029-v4/workspace/data/prepared/pilot/candidates/CHN) |
| Germany candidate conversations | 3,902 | [DEU](https://huggingface.co/datasets/memo-ozdincer/country-persona-aurora-data/tree/aurora-20261029-v4/workspace/data/prepared/pilot/candidates/DEU) |
| Combined SFT-format candidates | **16,373** | The two folders above, not an additional dataset |
| Focused canonical records | **37,094** | [Full JSONL](https://huggingface.co/datasets/memo-ozdincer/country-persona-aurora-data/resolve/aurora-20261029-v4/workspace/data/prepared/pilot/pilot.canonical.jsonl?download=true) |

Each country has four tasks: authentic Q&A, statement reconstruction, UPR recommendation and UPR response. Each task has train/dev/test SFT files with complete `prompt` and `completion` message lists, including the assistant answers, plus row-aligned provenance manifests. The 24 SFT files and 24 manifests are accompanied by the canonical pool, build report, duplicate ledger, admission CSV and split manifest: **53 original files / 335,534,335 bytes**.

The canonical pool contains broader evidence and overlapping source records. It is not 37,094 additional independent training conversations. The 16,373 rows are historical candidates, not newly expert-adjudicated or admitted examples. Original review/use statuses and all bytes are preserved; publication changes no admission decisions. See the original [data report](../../reports/DATA_REPORT.md), [data dictionary](../DATA_DICTIONARY.md) and [rights registry](../../data/rights_registry.json).

## Download this collection only

```python
from huggingface_hub import snapshot_download

snapshot_download(
    repo_id="memo-ozdincer/country-persona-aurora-data",
    repo_type="dataset",
    revision="aurora-20261029-v4",
    local_dir="country-persona-pilot",
    token=False,
    allow_patterns=[
        "workspace/data/prepared/pilot/**",
        "PILOT_MANIFEST.json",
        "VERIFY_PILOT_DOWNLOAD.py",
    ],
)
```

```bash
python3 -B country-persona-pilot/VERIFY_PILOT_DOWNLOAD.py
```

Expected: 53 files, 335,534,335 bytes verified. To restore the original layout, copy the downloaded `workspace/data/prepared/pilot/` into a fresh checkout's `data/prepared/pilot/`. Keep original manifests unchanged.

## Verification and scope

The original private archive was downloaded at pinned revision `bd8e2c90e72982ada3bdf2fad8137af9fa27a604`; its full SHA-256 and all 53 selected files matched the historical inventory. Every JSONL record was parsed, canonical IDs checked, SFT message structure checked, SFT/manifest row counts aligned, and all split counts matched the original build report. Credential scans passed before publication. All 53 remote content IDs/sizes matched, and anonymous China/Germany SFT downloads matched SHA-256. These are byte/schema/count checks, not new semantic review or model evaluation. [Exact publication receipt](../../reports/china-germany-pilot-publication-20261029-v1.json).

The original 15,826-file Aurora manifest is unchanged. The new `PILOT_MANIFEST.json` and verifier cover only these 53 added files. For the combined download, run both `VERIFY_DOWNLOAD.py` and `VERIFY_PILOT_DOWNLOAD.py`. Combined payload: **15,879 files / 6,778,439,838 bytes**. Other older raw/canonical collections outside this pilot remain outside this supplement. Research remains paused; no model calls, training or GPU use occurred.
