"""Replay available pinned draft and vote joins for the new Cyprus witness."""
import csv
from hashlib import sha256
import json
from pathlib import Path

import pyarrow.parquet as pq
from country_persona.unsc_bench import normalize_record

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]


def read(path):
    return json.loads(path.read_text())


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def run():
    UB = read(ROOT / "data/manifests/unbench-full-20260926.json")
    UC = read(ROOT / "data/manifests/unsc-bench-20260926.json")
    base = ROOT / UB["extraction_root"]
    draft = base / "drafts_adopted/2477/S_2023_64-EN.json"
    full = base / "all_drafts/1869/S_2023_64-EN.json"
    assert read(draft)["ID"] == read(full)["ID"] == "S/2023/64"
    rows = {}
    for split in ("train", "test"):
        path = base / f"task2_{split}_author.csv"
        with path.open(encoding="utf-8-sig", newline="") as stream:
            rows[split] = [(i, row["Country"], row["Voting"], row["Date"]) for i, row in enumerate(csv.DictReader(stream))
                           if row["Original_id"] == "2477"]
    assert not rows["train"] and len(rows["test"]) == 15
    assert {(vote, date) for _, _, vote, date in rows["test"]} == {("Y", "2023-01-30")}
    assert len({country for _, country, _, _ in rows["test"]}) == 15
    datasets = {}
    for config in ("adopted", "vetoed"):
        relative = f"{config}/data.parquet"
        raw = ROOT / UC["local_root"] / relative
        actual = digest(raw)
        assert actual == next(row["sha256"] for row in UC["files"] if row["path"] == relative)
        all_rows = pq.read_table(raw).to_pylist()
        matches = []
        for i, row in enumerate(all_rows):
            val = normalize_record(row, config, i)
            meeting = str(val.get("meeting") or "").removeprefix("S/PV.")
            if val["draft_symbol"] == "S/2023/64" or meeting == "9252":
                matches.append(i)
        datasets[config] = {"sha256": actual, "rows": len(all_rows), "matches": matches}
    return {"unbench": {"draft": str(draft.relative_to(ROOT)), "draft_sha256": digest(draft),
                        "all_draft_sha256": digest(full), "author_test_rows": rows["test"]},
            "unsc_bench": {"revision": UC["revision"], **datasets}}
if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
