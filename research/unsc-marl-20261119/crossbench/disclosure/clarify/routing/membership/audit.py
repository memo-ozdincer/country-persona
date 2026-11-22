"""Join the membership workshop anchor to the two pinned benchmark releases."""
import csv
from hashlib import sha256
import json
from pathlib import Path

import pyarrow.parquet as pq
from country_persona.unsc_bench import normalize_record

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[6]


def digest(p):
    return sha256(p.read_bytes()).hexdigest()


def audit():
    case = json.loads((HERE/"case.json").read_text())
    unbench = json.loads((ROOT/"data/manifests/unbench-full-20260926.json").read_text())
    raw_root = ROOT/unbench["extraction_root"]
    ub = raw_root/"all_drafts/1937/S_2024_312-EN.json"
    assert json.loads(ub.read_text())["ID"] == case["draft"]
    author = raw_root/"task2_test_author.csv"
    local_audit = json.loads((ROOT/"reports/eval-pilot-20260926/unbench-audit.json").read_text())
    assert digest(author) == local_audit["source_files_sha256"][author.name]
    with author.open(newline="",encoding="utf-8-sig") as f:
        indices = [i for i,r in enumerate(csv.DictReader(f)) if r["Original_id"]=="1937"]
    unsc = json.loads((ROOT/"data/manifests/unsc-bench-20260926.json").read_text())
    parquet = ROOT/unsc["local_root"]/"vetoed/data.parquet"
    expected = next(r["sha256"] for r in unsc["files"] if r["path"]=="vetoed/data.parquet")
    assert digest(parquet)==expected
    raw = pq.read_table(parquet).slice(7,1).to_pylist()[0]
    row = normalize_record(raw,"vetoed",7)
    assert not row["issues"] and row["draft_symbol"]==case["draft"] and row["date"]==case["date"]
    votes = {vote["country"]:vote["vote"] for vote in row["votes"]}
    assert (votes["FRANCE"],votes["UNITED KINGDOM"],votes["UNITED STATES"])==("Y","A","N")
    assert [sum(v==choice for v in votes.values()) for choice in ("Y","N","A")]==[12,1,2]
    return {"case_sha256":digest(HERE/"case.json"),
            "unbench":{"release_sha256":unbench["sha256"],"draft_sha256":digest(ub),
                       "original_id":"1937","author_test_vote_rows":indices},
            "unsc_bench":{"revision":unsc["revision"],"split":"vetoed","row":7,"file_sha256":expected,
                          "votes":votes,"official_record":case["historical"][0]["url"]}}


if __name__=="__main__":
    print(json.dumps(audit(),indent=2))
