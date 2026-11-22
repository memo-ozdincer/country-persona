"""Join Resolution 2721's official vote to the two pinned benchmark releases."""
import csv
from hashlib import sha256
import json
from pathlib import Path
import re

import pyarrow.parquet as pq

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
YES = ("ALBANIA", "BRAZIL", "ECUADOR", "FRANCE", "GABON", "GHANA", "JAPAN", "MALTA",
       "MOZAMBIQUE", "SWITZERLAND", "UNITED ARAB EMIRATES", "UNITED KINGDOM", "UNITED STATES")
OFFICIAL = dict.fromkeys(YES, "Y") | {"CHINA": "A", "RUSSIAN FEDERATION": "A"}


def read(path):
    return json.loads(path.read_text())


def digest(path):
    with path.open("rb") as raw:
        check = sha256()
        for block in iter(lambda: raw.read(1 << 20), b""):
            check.update(block)
    return check.hexdigest()


def symbol(text):
    return re.sub(r"\s+", "", str(text)).upper()


def run():
    manifest = ROOT/"data/manifests"
    ub = ROOT/read(manifest/"unbench-full-20260926.json")["extraction_root"]
    draft, = ub.glob("drafts_adopted/*/S_2023_1056-EN.json")
    assert read(draft)["ID"] == "S/2023/1056"
    code = draft.parent.name
    meeting = ub/f"meetings_adopted/{code}/S_PV.9521-EN.json"
    assert meeting.is_file()
    files, rows, votes = {}, {}, {}
    for name in ("train", "test"):
        path = ub/f"task2_{name}_author.csv"
        files[name] = digest(path)
        pinned = read(ROOT/"reports/eval-pilot-20260926/unbench-audit.json")["source_files_sha256"][path.name]
        assert files[name] == pinned
        with path.open(encoding="utf-8-sig", newline="") as raw:
            entries = [(i,r) for i,r in enumerate(csv.DictReader(raw)) if r["Original_id"] == code]
        rows[name] = [i for i,_ in entries]
        for _,r in entries:
            assert r["Country"] not in votes and r["Date"] == "2023-12-29"
            votes[r["Country"]] = r["Voting"]
    assert votes == OFFICIAL
    us = read(manifest/"unsc-bench-20260926.json")
    scans = {}
    targets = {"S/2023/1056", "S/PV.9521", "S/RES/2721(2023)"}
    for entry in us["files"]:
        if not entry["path"].endswith("data.parquet"):
            continue
        path = ROOT/us["local_root"]/entry["path"]
        actual = digest(path)
        assert actual == entry["sha256"]
        source = pq.read_table(path).to_pylist()
        hits = []
        for i,r in enumerate(source):
            fields = ((r.get("identifiers") or {}).get("symbol"),
                      (r.get("meeting") or {}).get("meeting_record"),
                      (r.get("draft_from_file1") or {}).get("draft_symbol"))
            if {symbol(x) for x in fields} & targets:
                hits.append(i)
        scans[entry["path"]] = {"rows":len(source),"matched_rows":hits,"sha256":actual}
    assert set(scans) == {"adopted/data.parquet","vetoed/data.parquet"}
    return {"draft":"S/2023/1056","meeting":"S/PV.9521","resolution":"S/RES/2721(2023)",
            "unbench_event":code,"unbench_rows":rows,"votes":dict(sorted(votes.items())),
            "unbench_hashes":{"draft":digest(draft),"meeting":digest(meeting),"author_csv":files},
            "unsc_bench":scans}


if __name__ == "__main__":
    print(json.dumps(run(),indent=2))
