"""Verify the pinned UNBench roll call and explicitly check UNSC-Bench coverage."""
from collections import Counter
import csv
from hashlib import sha256
import json
from pathlib import Path

import pyarrow.parquet as pq
from country_persona.unsc_bench import normalize_record

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
DRAFT="S/2022/980"
DATE="2022-12-21"
MEETING="9231"
ACT="S/RES/2669"


def load(path):
    return json.loads(path.read_text())


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def audit():
    ub=load(ROOT/"data/manifests/unbench-full-20260926.json")
    uc=load(ROOT/"data/manifests/unsc-bench-20260926.json")
    prior=load(ROOT/"reports/eval-pilot-20260926/unbench-audit.json")
    assert digest(ROOT/ub["file"])==ub["sha256"]
    source=ROOT/ub["extraction_root"]
    draft_paths=("all_drafts/1861/S_2022_980-EN.json","drafts_adopted/2472/S_2022_980-EN.json")
    assert all(load(source/p)["ID"]==DRAFT for p in draft_paths)
    by_split={}
    for subset in ("train","test"):
        path=source/f"task2_{subset}_author.csv"
        assert digest(path)==prior["source_files_sha256"][path.name]
        with path.open(encoding="utf-8-sig") as f:
            by_split[subset]=[(i,r) for i,r in enumerate(csv.DictReader(f),start=1)
                              if r["Original_id"]=="2472" and r["Date"]==DATE]
    assert len(by_split["test"])==15 and not by_split["train"]
    votes={r["Country"]:r["Voting"] for _,r in by_split["test"]}
    assert len(votes)==15 and Counter(votes.values())==Counter({"Y":12,"A":3})
    assert {k for k,v in votes.items() if v=="A"}=={"CHINA","INDIA","RUSSIAN FEDERATION"}
    release={}
    for subset in ("adopted","vetoed"):
        key=f"{subset}/data.parquet"
        file=ROOT/uc["local_root"]/key
        assert digest(file)==next(x["sha256"] for x in uc["files"] if x["path"]==key)
        tab=pq.read_table(file)
        matching=[]
        for index,item in enumerate(tab.to_pylist()):
            row=normalize_record(item,subset,index)
            identifier=str(item.get("identifiers", {}))
            if (row["draft_symbol"]==DRAFT or str(row["meeting"]).removeprefix("S/PV.")==MEETING
                or ACT in identifier or DRAFT in identifier):
                matching.append(index)
        release[subset]={"rows":len(tab),"matches":matching,"sha256":digest(file)}
    return {"unbench":{"archive_sha256":ub["sha256"],"author_test_rows":[i for i,_ in by_split["test"]],
                       "vote_date":DATE,"votes":votes,"drafts":{p:digest(source/p) for p in draft_paths}},
            "unsc_bench":{"revision":uc["revision"],"scans":release},
            "primary":{"roll_call":"https://digitallibrary.un.org/record/3998419?ln=en",
                       "meeting":"https://documents.un.org/api/symbol/access?l=en&s=S%2FPV.9231&t=pdf",
                       "act":"https://digitallibrary.un.org/record/3998406",
                       "resolution":"S/RES/2669 (2022)","draft":DRAFT}}


if __name__=="__main__":
    print(json.dumps(audit(),indent=2))
