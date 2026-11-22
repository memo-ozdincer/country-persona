"""Verify and freeze the UNBench draft and UNSC-Bench vote accession."""
import csv
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path

import pyarrow.parquet as pq

from country_persona.unsc_bench import normalize_record

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def build():
    task = read(HERE / "task.json")
    unbench = read(ROOT / "data/manifests/unbench-full-20260926.json")
    assert digest(ROOT / unbench["file"]) == unbench["sha256"]
    extracted = ROOT / unbench["extraction_root"]
    draft = extracted / "all_drafts/1722/S_2020_852-EN.json"
    assert read(draft)["ID"] == task["draft"] and read(draft)["Date"] == "31 August 2020"
    audited = read(ROOT / "reports/eval-pilot-20260926/unbench-audit.json")["source_files_sha256"]
    vote_tables = {}
    for split in ("train", "test"):
        path = extracted / f"task2_{split}_author.csv"
        sha = digest(path)
        assert sha == audited[path.name]
        with path.open(encoding="utf-8-sig", newline="") as stream:
            dates = Counter(row["Date"] for row in csv.DictReader(stream) if row["Original_id"] == "1722")
        vote_tables[split] = {"sha256": sha, "same_numeric_id_dates": dict(dates),
                              "matching_original_id_and_date": dates[task["date"]]}
    unsc = read(ROOT / "data/manifests/unsc-bench-20260926.json")
    relative = "vetoed/data.parquet"
    path = ROOT / unsc["local_root"] / relative
    sha = digest(path)
    assert sha == next(row["sha256"] for row in unsc["files"] if row["path"] == relative)
    raw = pq.read_table(path).slice(21, 1).to_pylist()[0]
    row = normalize_record(raw, "vetoed", 21)
    assert not row["issues"]
    assert (row["draft_symbol"], row["date"], row["meeting"]) == (task["draft"], task["date"], task["record"])
    votes = {vote["country"]: vote["vote"] for vote in row["votes"]}
    yes = ("BELGIUM|CHINA|DOMINICAN REPUBLIC|ESTONIA|FRANCE|GERMANY|INDONESIA|NIGER|RUSSIAN FEDERATION|"
           "SAINT VINCENT AND THE GRENADINES|SOUTH AFRICA|TUNISIA|UNITED KINGDOM|VIET NAM")
    assert votes == {**dict.fromkeys(yes.split("|"), "Y"), "UNITED STATES": "N"}
    return {"task_sha256": digest(HERE / "task.json"), "vote_transcription_source": task["sources"]["official_result"],
            "unbench": {"archive_sha256": unbench["sha256"], "draft_relative_path": str(draft.relative_to(extracted)),
                        "draft_sha256": digest(draft), "author_vote_tables": vote_tables},
            "unsc_bench": {"revision": unsc["revision"], "config": "vetoed", "row": 21, "sha256": sha},
            "verified_votes": votes}


if __name__ == "__main__":
    print(json.dumps(build(), indent=2))
