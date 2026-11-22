"""Replay the DRC draft and roll-call join against both pinned datasets."""
import argparse
import ast
import csv
from hashlib import sha256
import json
from pathlib import Path
import re

import pyarrow.parquet as pq
from country_persona.unsc_bench import country_name, normalize_record

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
EVENT = "2489"
DRAFT = "S/2023/469"
DATE = "2023-06-27"


def read(path):
    return json.loads(path.read_text())


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def build(official):
    ub = read(ROOT / "data/manifests/unbench-full-20260926.json")
    uc = read(ROOT / "data/manifests/unsc-bench-20260926.json")
    base = ROOT / ub["extraction_root"]
    checks = read(ROOT / "reports/eval-pilot-20260926/unbench-audit.json")["source_files_sha256"]
    rows = {}
    for split in ("train", "test"):
        path = base / f"task2_{split}_author.csv"
        assert checks[path.name] == digest(path)
        with path.open(encoding="utf-8-sig", newline="") as source:
            rows[split] = [(i, row) for i, row in enumerate(csv.DictReader(source)) if row["Original_id"] == EVENT]
    assert not rows["train"] and len(rows["test"]) == 15
    assert all(row["Date"] == DATE and ast.literal_eval(row["Authors"]) == ["France"] for _, row in rows["test"])
    votes = {row["Country"]: row["Voting"] for _, row in rows["test"]}
    draft = base / f"drafts_adopted/{EVENT}/S_2023_469-EN.json"
    assert read(draft)["ID"] == DRAFT
    data = ROOT / uc["local_root"] / "adopted/data.parquet"
    assert digest(data) == next(row["sha256"] for row in uc["files"] if row["path"] == "adopted/data.parquet")
    index = 254
    parsed = normalize_record(pq.read_table(data).slice(index, 1).to_pylist()[0], "adopted", index)
    assert (parsed["draft_symbol"], parsed["date"], parsed["meeting"]) == (DRAFT, DATE, "S/PV.9360")
    assert not parsed["issues"] and {v["country"]: v["vote"] for v in parsed["votes"]} == votes
    pp = read(official / "meeting.json")
    match = re.search(r"In favour: (.*?) The President: The draft resolution received 15 votes", pp[1])
    assert match and votes == {country_name(value.strip()): "Y" for value in match[1].split(",")}
    assert "adopted unanimously as resolution 2688 (2023)" in pp[1]
    resolutions = " ".join(read(official / "resolution.json"))
    assert all(x in resolutions for x in ("until 1 July 2024", "until 1 August 2024", "30 December 2023", "15 June 2024"))
    return {"event": EVENT, "unbench_test_rows": [i for i, _ in rows["test"]], "unbench_train_rows": [],
            "unbench_draft_sha256": digest(draft), "unsc_bench_adopted_row": index,
            "unsc_bench_revision": uc["revision"], "official_votes": votes,
            "source_pdf_sha256": {name: digest(official / f"{name}.pdf") for name in ("meeting", "resolution")},
            "case_sha256": digest(HERE / "case.json")}


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("official", type=Path)
    print(json.dumps(build(cli.parse_args().official), indent=2))
