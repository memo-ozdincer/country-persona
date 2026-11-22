"""Check UNBench and UNSC-Bench against the official 27 June 2024 vote."""
from collections import Counter
import csv
import json
from pathlib import Path
from hashlib import sha256

import pyarrow.parquet as parquet

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
DRAFT = "S/2024/500"
MEETING = "S/PV.9672"
RESOLUTION = "S/RES/2739 (2024)"
ABSTAIN = {"ALGERIA", "CHINA", "RUSSIAN FEDERATION"}


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return sha256(path.read_bytes()).hexdigest()


def run():
    ub = read(ROOT / "data/manifests/unbench-full-20260926.json")
    us = read(ROOT / "data/manifests/unsc-bench-20260926.json")
    audit = read(ROOT / "reports/eval-pilot-20260926/unbench-audit.json")
    dataset = ROOT / ub["extraction_root"]
    draft, = dataset.glob("drafts_adopted/*/S_2024_500-EN.json")
    event = draft.parent.name
    meeting = dataset / "meetings_adopted" / event / "S_PV.9672-EN_statements.json"
    assert read(draft)["Authors"] == "Japan and United States of America"
    assert DRAFT in read(meeting)["Content"]
    assert "adopted as resolution 2739 (2024)" in read(meeting)["Statements"][0]["statement"]
    files = [draft, meeting]
    rows, votes = {}, {}
    for split in ("train", "test"):
        file = dataset / f"task2_{split}_author.csv"
        assert sha(file) == audit["source_files_sha256"][file.name]
        files.append(file)
        with file.open(encoding="utf-8-sig", newline="") as stream:
            selected = [(i, r) for i, r in enumerate(csv.DictReader(stream)) if r["Original_id"] == event]
        rows[split] = [i for i, _ in selected]
        for _, row in selected:
            assert row["Date"] == "2024-06-27" and row["Country"] not in votes
            votes[row["Country"]] = row["Voting"]
    assert Counter(votes.values()) == {"Y": 12, "A": 3}
    assert {name for name, vote in votes.items() if vote == "A"} == ABSTAIN
    file = ROOT / us["local_root"] / "adopted/data.parquet"
    assert sha(file) == next(row["sha256"] for row in us["files"] if row["path"] == "adopted/data.parquet")
    files.append(file)
    adopted = parquet.read_table(file).to_pylist()
    matches = [(i, r) for i, r in enumerate(adopted)
               if r["identifiers"]["symbol"].replace(" ", "") == RESOLUTION.replace(" ", "")
               or r["meeting"]["meeting_record"] == MEETING or r["draft_from_file1"]["draft_symbol"] == DRAFT]
    if matches:
        (idx, row), = matches
        assert row["dates"]["vote_date"] == "2024-06-27"
        assert row["draft_from_file1"]["draft_symbol"] == DRAFT
        assert votes == {v["name"].upper(): v["vote"] for v in row["member_state_votes"]}
    else:
        idx = None
    return {"draft": DRAFT, "meeting": MEETING, "resolution": RESOLUTION,
            "unbench_event": event, "unbench_rows": rows, "pinned_unsc_bench_adopted_row": idx,
            "unsc_bench_rows_searched": len(adopted), "votes": votes,
            "sha256": {str(p.relative_to(ROOT)): sha(p) for p in files}}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
