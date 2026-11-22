"""Accession the three related UNBench instruments and their UNSC-Bench main vote."""
import csv
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path

import pyarrow.parquet as pq

from country_persona.unsc_bench import normalize_record

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
DRAFTS = {773: "1902", 775: "1901", 776: "1903"}


def read(path):
    return json.loads(path.read_text())


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def build():
    task = read(HERE / "task.json")
    ub = read(ROOT / "data/manifests/unbench-full-20260926.json")
    assert digest(ROOT / ub["file"]) == ub["sha256"]
    directory = ROOT / ub["extraction_root"]
    drafts = {}
    for symbol, identifier in DRAFTS.items():
        draft = directory / f"all_drafts/{identifier}/S_2023_{symbol}-EN.json"
        data = read(draft)
        assert data["ID"] == f"S/2023/{symbol}" and data["Date"] == "18 October 2023"
        drafts[data["ID"]] = {"id": identifier, "path": str(draft.relative_to(directory)), "sha256": digest(draft)}
    file_hashes = read(ROOT / "reports/eval-pilot-20260926/unbench-audit.json")["source_files_sha256"]
    votes_by_id = {}
    for split in ("train", "test"):
        file = directory / f"task2_{split}_author.csv"
        sha = digest(file)
        assert sha == file_hashes[file.name]
        with file.open(encoding="utf-8-sig", newline="") as stream:
            matches = Counter((row["Original_id"], row["Date"]) for row in csv.DictReader(stream)
                              if row["Original_id"] in DRAFTS.values())
        votes_by_id[split] = {"sha256": sha, "id_and_date_counts": {
            symbol: matches[entry["id"], task["date"]] for symbol, entry in drafts.items()}}
    sc = read(ROOT / "data/manifests/unsc-bench-20260926.json")
    relative = "vetoed/data.parquet"
    file = ROOT / sc["local_root"] / relative
    sha = digest(file)
    assert sha == next(row["sha256"] for row in sc["files"] if row["path"] == relative)
    vote = normalize_record(pq.read_table(file).slice(13, 1).to_pylist()[0], "vetoed", 13)
    assert not vote["issues"]
    assert (vote["draft_symbol"], vote["date"], vote["meeting"]) == (task["draft"], task["date"], "9442")
    observed = {row["country"]: row["vote"] for row in vote["votes"]}
    yes = "ALBANIA|BRAZIL|CHINA|ECUADOR|FRANCE|GABON|GHANA|JAPAN|MALTA|MOZAMBIQUE|SWITZERLAND|UNITED ARAB EMIRATES"
    assert observed == {**dict.fromkeys(yes.split("|"), "Y"), "UNITED STATES": "N", "RUSSIAN FEDERATION": "A",
                        "UNITED KINGDOM": "A"}
    return {"task_sha256": digest(HERE / "task.json"), "unbench": {"archive_sha256": ub["sha256"], "drafts": drafts,
             "author_tables": votes_by_id}, "unsc_bench": {"revision": sc["revision"], "row": 13, "config": "vetoed",
             "sha256": sha, "verified_votes": observed}, "primary_procedure": task["sources"]["meeting"]}


if __name__ == "__main__":
    print(json.dumps(build(), indent=2))
