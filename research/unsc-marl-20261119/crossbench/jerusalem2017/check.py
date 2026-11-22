"""Accession draft S/2017/1060 and the corresponding historical roll call."""
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
    relative = "all_drafts/1555/S_2017_1060-EN.json"
    draft = ROOT / ub["extraction_root"] / relative
    material = read(draft)
    assert (material["ID"], material["Date"]) == (task["draft"], "18 December 2017")
    sc = read(ROOT / "data/manifests/unsc-bench-20260926.json")
    source = "vetoed/data.parquet"
    roll = ROOT / sc["local_root"] / source
    assert digest(roll) == next(row["sha256"] for row in sc["files"] if row["path"] == source)
    vote = normalize_record(pq.read_table(roll).slice(30, 1).to_pylist()[0], "vetoed", 30)
    assert (vote["draft_symbol"].strip(), vote["date"], vote["meeting"]) == (task["draft"], task["date"], "8139")
    assert not vote["issues"]
    votes = {row["country"]: row["vote"] for row in vote["votes"]}
    assert len(votes) == 15 and votes["UNITED STATES"] == "N" and list(votes.values()).count("Y") == 14
    return {"task_sha256": digest(HERE / "task.json"),
            "unbench": {"path": relative, "sha256": digest(draft), "archive_sha256": ub["sha256"]},
            "unsc_bench": {"config": "vetoed", "row": 30, "revision": sc["revision"], "sha256": digest(roll),
                           "raw_symbol": vote["draft_symbol"], "verified_votes": votes},
            "procedure": task["sources"]["meeting"]}


if __name__ == "__main__":
    print(json.dumps(build(), ensure_ascii=False, indent=2))
