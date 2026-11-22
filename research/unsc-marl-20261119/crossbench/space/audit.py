"""Pin release provenance and verify the April draft against the official roll call."""
from collections import Counter
import csv
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
    unbench = read(ROOT / "data/manifests/unbench-full-20260926.json")
    assert digest(ROOT / unbench["file"]) == unbench["sha256"]
    extracted = ROOT / unbench["extraction_root"]
    ids = {"S/2024/302": "1938", "S/2024/323": "1939", "S/2024/383": "1941"}
    corpus = {}
    for symbol, key in ids.items():
        path = extracted / "all_drafts" / key / (symbol.replace("/", "_") + "-EN.json")
        assert read(path)["ID"] == symbol
        corpus[symbol] = {"path": str(path.relative_to(extracted)), "sha256": digest(path), "task2_matches": 0}
    expected_dates = {"1938": "2024-04-24", "1939": "2024-04-24", "1941": "2024-05-20"}
    by_id = {v: k for k, v in ids.items()}
    audit = read(ROOT / "reports/eval-pilot-20260926/unbench-audit.json")
    for split in ("train", "test"):
        path = extracted / f"task2_{split}_author.csv"
        assert digest(path) == audit["source_files_sha256"][path.name]
        with path.open(encoding="utf-8-sig", newline="") as fh:
            for row in csv.DictReader(fh):
                key = row["Original_id"]
                if expected_dates.get(key) == row["Date"]:
                    corpus[by_id[key]]["task2_matches"] += 1
    assert all(row["task2_matches"] == 0 for row in corpus.values())

    unsc = read(ROOT / "data/manifests/unsc-bench-20260926.json")
    relative = "vetoed/data.parquet"
    source = ROOT / unsc["local_root"] / relative
    assert digest(source) == next(item["sha256"] for item in unsc["files"] if item["path"] == relative)
    row = normalize_record(pq.read_table(source).slice(6, 1).to_pylist()[0], "vetoed", 6)
    votes = {v["country"]: v["vote"] for v in row["votes"]}
    assert not row["issues"] and row["draft_symbol"] == "S/2024/302" and row["date"] == "2024-04-24"
    assert str(row["meeting"]).removeprefix("S/PV.") == "9616"
    support = ("ALGERIA|ECUADOR|FRANCE|GUYANA|JAPAN|MALTA|MOZAMBIQUE|REPUBLIC OF KOREA|"
               "SIERRA LEONE|SLOVENIA|SWITZERLAND|UNITED KINGDOM|UNITED STATES")
    assert votes == {**dict.fromkeys(support.split("|"), "Y"), "RUSSIAN FEDERATION": "N", "CHINA": "A"}
    amendment_yes = "ALGERIA|ECUADOR|CHINA|GUYANA|MOZAMBIQUE|RUSSIAN FEDERATION|SIERRA LEONE"
    amendment_no = "FRANCE|JAPAN|MALTA|REPUBLIC OF KOREA|SLOVENIA|UNITED KINGDOM|UNITED STATES"
    broader = {**dict.fromkeys(amendment_yes.split("|"), "Y"), **dict.fromkeys(amendment_no.split("|"), "N"),
               "SWITZERLAND": "A"}
    assert Counter(broader.values()) == Counter(Y=7, N=7, A=1)
    april = "https://digitallibrary.un.org/record/4045546/files/S_PV.9616-EN.pdf"
    may = "https://digitallibrary.un.org/record/4049130/files/S_PV.9630-EN.pdf"
    return {
        "family": "outer-space-2024",
        "unbench_archive_sha256": unbench["sha256"],
        "unbench_draft_provenance": corpus,
        "unsc_bench": {"revision": unsc["revision"], "config": "vetoed", "row_index": 6,
                       "file_sha256": digest(source)},
        "retrospective_references": {
            "S/2024/323": {"meeting": april, "stage": "amendment", "votes": broader,
                           "disposition": "not adopted, fewer than nine affirmative votes"},
            "S/2024/302": {"meeting": april, "stage": "final draft", "votes": votes,
                           "disposition": "not adopted, negative vote of a permanent member"},
            "S/2024/383": {"meeting": may, "stage": "later standalone draft", "votes": broader,
                           "disposition": "not adopted, fewer than nine affirmative votes"},
        },
    }


if __name__ == "__main__":
    print(json.dumps(build(), indent=2, sort_keys=True))
