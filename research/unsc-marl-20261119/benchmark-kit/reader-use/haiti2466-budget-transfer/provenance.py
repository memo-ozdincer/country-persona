"""Verify the draft, date and roll call joins to both pinned benchmarks."""
import csv
from hashlib import sha256
import json
from pathlib import Path
import subprocess

import pyarrow.parquet as pq

from run_transfer import PACKET, read

ROOT = Path(subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip())


def run():
    packet = read(PACKET)
    event = packet["event"]
    ub = read(ROOT / "data/manifests/unbench-full-20260926.json")
    us = read(ROOT / "data/manifests/unsc-bench-20260926.json")
    data = ROOT / us["local_root"] / "adopted/data.parquet"
    index = event["unsc_bench_adopted_index"]
    row, = pq.ParquetFile(data).read().slice(index, 1).to_pylist()
    assert row["dates"]["vote_date"] == event["date"]
    assert row["meeting"]["meeting_record"] == event["meeting"]
    assert row["draft_from_file1"]["draft_symbol"] == event["draft"]
    assert row["identifiers"]["symbol"] == event["resolution"]
    assert row["urls_meeting"]["en"] == packet["official"]["meeting"]
    assert row["urls_resolution"]["en"] == packet["official"]["resolution"]
    directory = ROOT / ub["extraction_root"]
    seen = {}
    for split in ("train","test"):
        with (directory / f"task2_{split}_author.csv").open(encoding="utf-8-sig", newline="") as stream:
            seen[split] = [(i, r) for i, r in enumerate(csv.DictReader(stream)) if r["Original_id"] == event["unbench"]]
    assert not seen["train"] and len(seen["test"]) == 15
    assert {r["Date"] for _, r in seen["test"]} == {event["date"]}
    votes = {r["Country"].upper(): r["Voting"] for _, r in seen["test"]}
    assert votes == {r["name"].upper(): r["vote"] for r in row["member_state_votes"]}
    assert {k for k,v in votes.items() if v == "A"} == {"DOMINICAN REPUBLIC","RUSSIAN FEDERATION"}
    assert sum(v == "Y" for v in votes.values()) == 13 and set(votes.values()) == {"Y","A"}
    draft = directory / "drafts_adopted" / event["unbench"] / "S_2019_311-EN.json"
    digest = sha256(data.read_bytes()).hexdigest()
    assert digest == next(f["sha256"] for f in us["files"] if f["path"] == "adopted/data.parquet")
    return {"event": event, "unbench_author_test_rows": [i for i, _ in seen["test"]],
            "unbench_draft": str(draft.relative_to(ROOT)), "unbench_draft_sha256": sha256(draft.read_bytes()).hexdigest(),
            "unsc_bench_revision": us["revision"], "unsc_bench_sha256": digest, "votes": votes,
            "official": packet["official"]}


if __name__ == "__main__":
    print(json.dumps(run(),ensure_ascii=False,indent=2))
