"""Join the new case to the project's pinned UNBench and UNSC-Bench copies."""
from collections import Counter
import csv
from hashlib import sha256
import json
from pathlib import Path

import pyarrow.parquet as parquet

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
DRAFT = "S/2024/557"
MEETING = "S/PV.9689"
RESOLUTION = "S/RES/2744 (2024)"
DATE = "2024-07-19"


def read(path):
    return json.loads(path.read_text())


def pin(path):
    return sha256(path.read_bytes()).hexdigest()


def run():
    ub = read(ROOT/"data/manifests/unbench-full-20260926.json")
    us = read(ROOT/"data/manifests/unsc-bench-20260926.json")
    audit = read(ROOT/"reports/eval-pilot-20260926/unbench-audit.json")
    dataset = ROOT/ub["extraction_root"]
    draft, = dataset.glob("drafts_adopted/*/S_2024_557-EN.json")
    event = draft.parent.name
    meeting = dataset/"meetings_adopted"/event/"S_PV.9689-EN_statements.json"
    assert {"Malta", "United States of America"} <= set(read(draft)["Authors"])
    text = " ".join(read(meeting)["Content"].split())
    assert DRAFT in text and "2744 (2024)" in text and "15 votes in favour" in text
    files = [draft, meeting]
    rows, votes = {}, {}
    for split in ("train","test"):
        file = dataset/f"task2_{split}_author.csv"
        assert pin(file) == audit["source_files_sha256"][file.name]
        files.append(file)
        with file.open(encoding="utf-8-sig", newline="") as stream:
            selected = [(i, r) for i,r in enumerate(csv.DictReader(stream)) if r["Original_id"]==event]
        rows[split] = [i for i,_ in selected]
        for _, row in selected:
            assert row["Date"]==DATE and row["Country"] not in votes
            votes[row["Country"]]=row["Voting"]
    assert Counter(votes.values()) == {"Y":15}
    file = ROOT/us["local_root"]/"adopted/data.parquet"
    assert pin(file) == next(r["sha256"] for r in us["files"] if r["path"]=="adopted/data.parquet")
    files.append(file)
    adopted = parquet.read_table(file).to_pylist()
    matches = [(i,r) for i,r in enumerate(adopted) if
               r["identifiers"]["symbol"].replace(" ","")==RESOLUTION.replace(" ","")
               or r["meeting"]["meeting_record"]==MEETING or r["draft_from_file1"]["draft_symbol"]==DRAFT]
    match = None
    if matches:
        (match, row),=matches
        assert row["dates"]["vote_date"]==DATE
        assert row["draft_from_file1"]["draft_symbol"]==DRAFT
        assert votes == {r["name"].upper():r["vote"] for r in row["member_state_votes"]}
    return {"meeting": MEETING,"draft":DRAFT,"resolution":RESOLUTION,
            "unbench_event":event,"unbench_rows":rows,"votes":votes,
            "unsc_bench_adopted_row":match,"unsc_bench_rows_searched":len(adopted),
            "verified_source_files":{str(p.relative_to(ROOT)):pin(p) for p in files}}


if __name__ == "__main__":
    print(json.dumps(run(),indent=2))
