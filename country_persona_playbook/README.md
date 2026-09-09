# Country-persona post-training starter kit

**Research inspection date: 9 September 2026.** Target: a dated institutional representative in a research simulation—not a national stereotype or a claim to be an actual official.

## Start here

Read `playbook.md` for the experimental design and prioritized data sources. Use `sources.csv` / `sources.json` to assign acquisition work, and `methods.csv` for the papers and code to reuse. `schemas.md` distinguishes inspected upstream formats from proposed training formats.

The package contains **23 source entries and 9 method/codebase entries**. Counts describe the registry, not 23 acquired datasets. Full source corpora and third-party model weights are **not** included.

## What actually runs here

`src/prepare.py` uses only Python 3.10+ standard-library modules. It converts the inspected UNBench task-2/task-4 structures, explicitly mapped QA CSV files, and extracted UNGDC TXT files. New records enter quarantine. A human-reviewed CSV and a reserved-group list are required before SFT export. The export includes an aligned provenance manifest.

Twelve local unit tests passed on invented fixtures. They test conversion, missing joins, quarantine, permission gates, exact-text overlap, group leakage, and reserved evaluation groups. This is **not** a full-data validation run. The single-GPU QLoRA `src/train_sft.py` starter was checked against the linked documentation and compiled, but **not executed on a GPU**. No end-to-end model-training result is claimed.

## Quick start: local test

```bash
python -m unittest discover -s tests -v
```

## Acquire and inspect UNBench samples

The following network commands are intended for your machine; network acquisition was not tested in this package.

```bash
mkdir -p external canonical review prepared
# Review the repo licence AND the underlying UN source terms before training.
git clone https://github.com/yueqingliang1/UNBench external/UNBench
git -C external/UNBench rev-parse HEAD > external/UNBench.revision.txt

python src/prepare.py unbench-task2 \
  --input external/UNBench/data/task2.csv \
  --drafts-dir external/UNBench/data/task2 \
  --output canonical/unbench_votes.jsonl

python src/prepare.py unbench-task4 \
  --input external/UNBench/data/task4.json \
  --output canonical/unbench_statements.jsonl
```

The GitHub data are samples, not the entire UNBench release. The authors link the full archive in the README. Do not train on evaluation items just to exercise the pipeline; use invented fixtures for plumbing tests.

## Review and export

```bash
python src/prepare.py review-template \
  --input canonical/unbench_votes.jsonl \
  --output review/votes.csv
```

Review every admitted source/record. Fill the reviewed country code, group identity, institutional capacity, phase, split, permissions decision and reviewer. `source_verified` and `context_asof_verified` mean an actual provenance and time-availability check, not simply that a URL exists. Keep the benchmark evaluation subset quarantined/test. Edit `config/reserved_groups.txt` to contain the locked meeting/resolution-family groups; the supplied file is only a template.

```bash
python src/prepare.py build-sft \
  --input canonical/unbench_votes.jsonl \
  --review review/votes.csv \
  --reserved-groups config/reserved_groups.txt \
  --output-dir prepared/votes
```

The builder deliberately fails when no approved examples exist. It does not silently label public data as permitted training data.

## Other converters

For an extracted UNGDC folder:

```bash
python src/prepare.py ungdc --input external/ungdc \
  --output canonical/ungdc.jsonl
```

This emits **domain-text records**, not fabricated instruction pairs. Filename years remain year-precision, not invented January 1 dates.

For a QA CSV after inspecting its real column names:

```bash
python src/prepare.py qa-csv \
  --input external/reviewed_qa.csv --output canonical/qa.jsonl \
  --id-col RECORD_ID --group-col CONFERENCE_ID --date-col EVENT_DATE \
  --question-col QUESTION --answer-col ANSWER \
  --country 'COUNTRY_NAME' --source-id SOURCE_SLUG \
  --source-url 'https://SOURCE_LANDING_PAGE' \
  --institution FOREIGN_MINISTRY --capacity spokesperson --language en
```

Uppercase column names above are placeholders, **not claimed headers of the Chinese MFA corpus**. The published file headers could not be fetched. Follow-up questions require their earlier context, which this generic row adapter does not reconstruct automatically.

## SFT starter

Use your lab’s compatible GPU environment, install the dependencies in `requirements-training.in`, smoke-test 10–20 approved examples, and lock actual versions. The code follows the TRL documentation inspected on the date above; it is not a tested environment lockfile.

```bash
python src/train_sft.py \
  --model /path/to/your-instruction-checkpoint \
  --data prepared/votes/train.sft.jsonl \
  --manifest prepared/votes/train.manifest.jsonl \
  --output runs/shared-country-sft \
  --max-length 4096 --epochs 1 --lr 1e-4 --lora-rank 16
```

These are pilot settings, not tuned recommendations or GPU-memory guarantees. Long resolutions may exceed the context budget: the script aborts rather than silently truncate the target. It is a single-GPU QLoRA starter, not a distributed trainer or an experiment sweeper. Choose checkpoints by separate held-out evaluation; do not repeatedly tune on the final test set.

## What is not implemented

No browser crawler, retrieval index, automatic country/entity reconciliation, near-duplicate semantic detector, UPR/UHRI importer, DPO trainer, episode simulator, or medical-data importer is claimed. Those parts are specified in the playbook. Do not mistake a documented source or proposed schema for an acquired/validated dataset. Raw archives blocked by access controls were not bypassed.

## References and permissions

All registry entries include source URLs, inspection level, acquisition notes and rights notes. Follow each source’s permissions and attribution requirements. The official UNGA voting release expressly specifies non-commercial use with attribution. Public availability does not establish commercial reuse rights, nor does a code repository’s licence settle rights in all data it contains.
