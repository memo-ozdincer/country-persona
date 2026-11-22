"""Verify the Haiti draft, roll call and archive membership."""
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


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def build(official):
    unbench = read(ROOT / "data/manifests/unbench-full-20260926.json")
    unsc = read(ROOT / "data/manifests/unsc-bench-20260926.json")
    audit = read(ROOT / "reports/eval-pilot-20260926/unbench-audit.json")
    base = ROOT / unbench["extraction_root"]
    rows = {}
    for split in ("train", "test"):
        path = base / f"task2_{split}_author.csv"
        assert digest(path) == audit["source_files_sha256"][path.name]
        with path.open(encoding="utf-8-sig", newline="") as file:
            rows[split] = [(i, r) for i, r in enumerate(csv.DictReader(file)) if r["Original_id"] == "2501"]
    assert not rows["train"] and len(rows["test"]) == 15
    votes = {r["Country"]: r["Voting"] for _, r in rows["test"]}
    assert all(r["Date"] == "2023-10-02" and set(ast.literal_eval(r["Authors"])) == {"United States", "Ecuador"}
               for _, r in rows["test"])
    draft = base / "drafts_adopted/2501/S_2023_709-EN.json"
    assert read(draft)["ID"] == "S/2023/709"
    relative = "adopted/data.parquet"
    data = ROOT / unsc["local_root"] / relative
    assert digest(data) == next(row["sha256"] for row in unsc["files"] if row["path"] == relative)
    index = 242
    normalized = normalize_record(pq.read_table(data).slice(index, 1).to_pylist()[0], "adopted", index)
    assert normalized["draft_symbol"] == "S/2023/709" and normalized["meeting"] == "S/PV.9430"
    assert normalized["date"] == "2023-10-02" and not normalized["issues"]
    assert {row["country"]: row["vote"] for row in normalized["votes"]} == votes
    pages = read(official / "meeting.json")
    match = re.search(r"In favour: (.*?) Against: None Abstaining: (.*?) The President:", pages[1])
    assert match
    identified = {country_name(name.strip()): vote for group, vote in zip(match.groups(), ("Y", "A"), strict=True)
                  for name in group.split(",")}
    assert identified == votes
    assert "adopted as resolution 2699 (2023)" in pages[1]
    assert "on behalf of the three African members" in pages[4]
    resolution = " ".join(read(official / "resolution.json"))
    assert all(span in resolution for span in ("initial period of twelve months", "reviewed nine months",
                                               "voluntary contributions", "establish an oversight mechanism"))
    return {"unbench_event": "2501", "unbench_test_rows": [i for i, _ in rows["test"]],
            "unbench_draft_sha256": digest(draft), "unsc_bench_revision": unsc["revision"],
            "unsc_bench_adopted_row": index, "official_vote_labels": votes,
            "primary_pdf_sha256": {name: digest(official / f"{name}.pdf") for name in ("meeting", "resolution")},
            "case_sha256": digest(HERE / "case.json")}


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("official", type=Path)
    print(json.dumps(build(cli.parse_args().official), indent=2))
