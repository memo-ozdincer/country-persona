"""Verify the pinned UNBench draft and UNSC-Bench roll call for S/2021/990."""
import csv
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path

import pyarrow.parquet as pq

from country_persona.unsc_bench import normalize_record

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]


def read(path):
    return json.loads(path.read_text())


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def build():
    task = read(HERE / "task.json")
    ub = read(ROOT / "data/manifests/unbench-full-20260926.json")
    assert digest(ROOT / ub["file"]) == ub["sha256"]
    directory = ROOT / ub["extraction_root"]
    draft = directory / "all_drafts/1793/S_2021_990-EN.json"
    assert read(draft)["ID"] == task["draft"] and read(draft)["Date"] == "13 December 2021"
    known = read(ROOT / "reports/eval-pilot-20260926/unbench-audit.json")["source_files_sha256"]
    table_matches = {}
    for split in ("train", "test"):
        path = directory / f"task2_{split}_author.csv"
        file_hash = digest(path)
        assert file_hash == known[path.name]
        with path.open(encoding="utf-8-sig", newline="") as stream:
            dates = Counter(row["Date"] for row in csv.DictReader(stream) if row["Original_id"] == "1793")
        table_matches[split] = {"sha256": file_hash, "dates_with_same_numeric_id": dict(dates),
                                "matches_by_id_and_date": dates[task["date"]]}
    sc = read(ROOT / "data/manifests/unsc-bench-20260926.json")
    data_path = "vetoed/data.parquet"
    file = ROOT / sc["local_root"] / data_path
    file_hash = digest(file)
    assert file_hash == next(row["sha256"] for row in sc["files"] if row["path"] == data_path)
    vote = normalize_record(pq.read_table(file).slice(20, 1).to_pylist()[0], "vetoed", 20)
    assert not vote["issues"] and vote["draft_symbol"] == task["draft"] and vote["date"] == task["date"]
    assert str(vote["meeting"]).removeprefix("S/PV.") == task["meeting"].removeprefix("S/PV.")
    votes = {row["country"]: row["vote"] for row in vote["votes"]}
    yes = ("ESTONIA|FRANCE|IRELAND|KENYA|MEXICO|NIGER|NORWAY|SAINT VINCENT AND THE GRENADINES|"
           "TUNISIA|UNITED KINGDOM|UNITED STATES|VIET NAM")
    assert votes == {**dict.fromkeys(yes.split("|"), "Y"), "INDIA": "N", "RUSSIAN FEDERATION": "N", "CHINA": "A"}
    return {"task_sha256": digest(HERE / "task.json"),
            "unbench": {"archive_sha256": ub["sha256"], "draft": str(draft.relative_to(directory)),
                        "draft_sha256": digest(draft), "author_tables": table_matches},
            "unsc_bench": {"revision": sc["revision"], "config": "vetoed", "row": 20, "sha256": file_hash},
            "verified_votes": votes, "primary_record": task["sources"]["meeting"]}


if __name__ == "__main__":
    print(json.dumps(build(), indent=2))
