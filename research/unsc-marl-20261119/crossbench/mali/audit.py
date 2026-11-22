"""Join the Mali drafts to the pinned releases and audited primary roll call."""
import csv
import json
from pathlib import Path
import sys

import pyarrow.parquet as pq
from country_persona.unsc_bench import normalize_record

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "space"))
from audit import ROOT, read, digest


def build():
    unbench = read(ROOT / "data/manifests/unbench-full-20260926.json")
    unsc = read(ROOT / "data/manifests/unsc-bench-20260926.json")
    extract = ROOT / unbench["extraction_root"]
    assert digest(ROOT / unbench["file"]) == unbench["sha256"]
    expected = {"1893": "S/2023/638", "1894": "S/2023/639"}
    drafts = {}
    for key, symbol in expected.items():
        path = extract / f"all_drafts/{key}/{symbol.replace('/', '_')}-EN.json"
        assert read(path)["ID"] == symbol
        drafts[symbol] = {"path": str(path.relative_to(extract)), "sha256": digest(path)}
    counts = {}
    old_audit = read(ROOT / "reports/eval-pilot-20260926/unbench-audit.json")
    for split in ("train", "test"):
        path = extract / f"task2_{split}_author.csv"
        assert digest(path) == old_audit["source_files_sha256"][path.name]
        with path.open(encoding="utf-8-sig") as fh:
            counts[split] = sum(r["Original_id"] in expected and r["Date"] == "2023-08-30"
                                for r in csv.DictReader(fh))
    relative = "vetoed/data.parquet"
    path = ROOT / unsc["local_root"] / relative
    assert digest(path) == next(f["sha256"] for f in unsc["files"] if f["path"] == relative)
    row = normalize_record(pq.read_table(path).slice(14, 1).to_pylist()[0], "vetoed", 14)
    votes = {v["country"]: v["vote"] for v in row["votes"]}
    members = "ALBANIA|BRAZIL|ECUADOR|FRANCE|GABON|GHANA|JAPAN|MALTA|MOZAMBIQUE|SWITZERLAND|UNITED ARAB EMIRATES|UNITED KINGDOM|UNITED STATES"
    assert not row["issues"] and row["draft_symbol"] == "S/2023/638" and row["date"] == "2023-08-30"
    assert str(row["meeting"]).removeprefix("S/PV.") == "9408"
    assert votes == {**dict.fromkeys(members.split("|"), "Y"), "CHINA": "A", "RUSSIAN FEDERATION": "N"}
    return {"family": "mali-experts-2023", "unbench_archive_sha256": unbench["sha256"],
            "unbench_drafts": drafts, "unbench_task2_number_and_date_matches": counts,
            "unsc_bench": {"revision": unsc["revision"], "row": 14, "split": "vetoed", "votes": votes},
            "primary": "https://digitallibrary.un.org/record/4020239/files/S_PV.9408-EN.pdf",
            "dispositions": {"S/2023/638": "13–1–1, negative vote of a permanent member",
                             "S/2023/639": "1–1–13, insufficient affirmative votes"}}


if __name__ == "__main__":
    print(json.dumps(build(), indent=2, ensure_ascii=False))
