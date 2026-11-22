"""Join the official Resolution 2686 instruments to the pinned benchmark releases."""
from hashlib import sha256
import csv
import json
from pathlib import Path

import pyarrow.parquet as pq

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
EVENT = {"draft": "S/2023/427", "meeting": "S/PV.9347", "resolution": "S/RES/2686 (2023)", "date": "2023-06-14"}


def read(file):
    return json.loads(file.read_text())


def digest(file):
    checksum = sha256()
    with file.open("rb") as raw:
        for block in iter(lambda: raw.read(2 ** 20), b""):
            checksum.update(block)
    return checksum.hexdigest()


def run():
    ub = read(ROOT / "data/manifests/unbench-full-20260926.json")
    us = read(ROOT / "data/manifests/unsc-bench-20260926.json")
    meta = read(ROOT / "reports/eval-pilot-20260926/unbench-audit.json")
    source = ROOT / ub["extraction_root"]
    draft, = source.glob("drafts_adopted/*/S_2023_427-EN.json")
    assert read(draft)["ID"] == EVENT["draft"]
    code = draft.parent.name
    matched, files = {}, {}
    for split in ("train", "test"):
        doc = source / f"task2_{split}_author.csv"
        files[split] = digest(doc)
        assert files[split] == meta["source_files_sha256"][doc.name]
        with doc.open(encoding="utf-8-sig", newline="") as raw:
            matched[split] = [(i, row) for i, row in enumerate(csv.DictReader(raw)) if row["Original_id"] == code]
    votes = {row["Country"]: row["Voting"] for data in matched.values() for _, row in data}
    assert len(votes) == sum(map(len, matched.values())) == 15 and set(votes.values()) == {"Y"}
    assert {r["Date"] for data in matched.values() for _, r in data} == {EVENT["date"]}
    table = ROOT / us["local_root"] / "adopted/data.parquet"
    actual_hash = digest(table)
    assert actual_hash == next(item["sha256"] for item in us["files"] if item["path"] == "adopted/data.parquet")
    rows = pq.read_table(table).to_pylist()
    matches = [(i, r) for i, r in enumerate(rows)
               if r["identifiers"]["symbol"].replace(" ", "") == EVENT["resolution"].replace(" ", "")
               or str(r["meeting"]["meeting_record"]).removeprefix("S/PV.") == "9347"
               or r["draft_from_file1"]["draft_symbol"] == EVENT["draft"]]
    row_id = None
    if matches:
        (row_id, row), = matches
        assert row["draft_from_file1"]["draft_symbol"] == EVENT["draft"] and row["dates"]["vote_date"] == EVENT["date"]
        assert votes == {r["name"]: r["vote"] for r in row["member_state_votes"]}
    return {"event": EVENT, "unbench_event": code, "unbench_row_indices": {
        split: [i for i, _ in data] for split, data in matched.items()},
        "unsc_bench_adopted_row": row_id, "unsc_bench_adopted_rows_searched": len(rows),
        "votes": dict(sorted(votes.items())),
        "source_hashes": {"draft": digest(draft), "unbench_vote_csv": files, "unsc_adopted": actual_hash}}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
