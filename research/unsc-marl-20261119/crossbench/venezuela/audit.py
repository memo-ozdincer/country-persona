"""Join the source-checked Venezuela drafts to both pinned benchmark releases."""
import csv
from hashlib import file_digest
import json
from pathlib import Path
import unicodedata

import pyarrow.parquet as pq
from country_persona.unsc_bench import normalize_record

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
DRAFTS={"S/2019/186":"1630","S/2019/190":"1629"}


def load(path):
    return json.loads(path.read_text())


def digest(path):
    with path.open("rb") as file:
        return file_digest(file,"sha256").hexdigest()


def country(name):
    normalized=unicodedata.normalize("NFKD",name.upper().replace("’","'"))
    return "".join(c for c in normalized if not unicodedata.combining(c))


def build():
    facts=load(HERE/"facts.json")
    roster={symbol:{country(k):vote for key,vote in (("in_favour","Y"),("against","N"),("abstaining","A"))
                    for k in row[key]} for symbol,row in facts["votes"].items()}
    assert all(len(r)==15 for r in roster.values())
    assert set(roster["S/2019/186"])==set(roster["S/2019/190"])
    ub=load(ROOT/"data/manifests/unbench-full-20260926.json")
    uc=load(ROOT/"data/manifests/unsc-bench-20260926.json")
    old=load(ROOT/"reports/eval-pilot-20260926/unbench-audit.json")
    assert digest(ROOT/ub["file"])==ub["sha256"]
    extract=ROOT/ub["extraction_root"]
    files={}
    for symbol,key in DRAFTS.items():
        path=extract/"all_drafts"/key/(symbol.replace("/","_")+"-EN.json")
        assert load(path)["ID"]==symbol
        files[symbol]={"file":str(path.relative_to(extract)),"sha256":digest(path)}
    id_to_symbol={v:k for k,v in DRAFTS.items()}
    by_split={}
    for split in ("train","test"):
        path=extract/f"task2_{split}_author.csv"
        assert digest(path)==old["source_files_sha256"][path.name]
        with path.open(encoding="utf-8-sig",newline="") as file:
            rows={symbol:[] for symbol in DRAFTS}
            for i,r in enumerate(csv.DictReader(file),1):
                if r["Date"]==facts["date"] and r["Original_id"] in id_to_symbol:
                    symbol=id_to_symbol[r["Original_id"]]
                    member=country(r["Country"])
                    assert roster[symbol][member]==r["Voting"]
                    rows[symbol].append({"record":i,"member":member,"vote":r["Voting"]})
        by_split[split]=rows
    unsc={}
    for split in ("adopted","vetoed"):
        relative=f"{split}/data.parquet"
        path=ROOT/uc["local_root"]/relative
        assert digest(path)==next(f["sha256"] for f in uc["files"] if f["path"]==relative)
        collection=pq.read_table(path).to_pylist()
        matches=[]
        for i,raw in enumerate(collection):
            normalized=normalize_record(raw,split,i)
            if (normalized["draft_symbol"] not in DRAFTS
                    and str(normalized["meeting"]).removeprefix("S/PV.")!="8476"):
                continue
            votes={country(row["country"]):row["vote"] for row in normalized["votes"]}
            symbol=normalized["draft_symbol"]
            assert normalized["date"]==facts["date"]
            assert symbol in roster and votes==roster[symbol] and not normalized["issues"]
            matches.append({"row":i,"symbol":symbol,"votes":votes})
        unsc[split]={"rows":len(collection),"sha256":digest(path),"matches":matches}
    return {"family":facts["family"],"primary":facts["sources"],"roll_calls":roster,
            "unbench":{"archive_sha256":ub["sha256"],"drafts":files,"task2_author":by_split},
            "unsc_bench":{"revision":uc["revision"],"splits":unsc}}


if __name__=="__main__":
    print(json.dumps(build(),indent=2))
