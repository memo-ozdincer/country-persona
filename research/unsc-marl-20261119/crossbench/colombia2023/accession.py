"""Verify the Colombia docket against the pinned benchmark releases."""
import argparse
import ast
import csv
from hashlib import sha256
import json
from pathlib import Path
import re

import pyarrow.parquet as pq

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
EVENT = "2504"
DATE = "2023-10-30"
SYMBOL = "S/2023/808"


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def build(pdfs):
    unbench = read(ROOT / "data/manifests/unbench-full-20260926.json")
    unsc = read(ROOT / "data/manifests/unsc-bench-20260926.json")
    audit = read(ROOT / "reports/eval-pilot-20260926/unbench-audit.json")
    base = ROOT / unbench["extraction_root"]
    paths = {key: base / f"task2_{key}_author.csv" for key in ("train", "test")}
    match = {}
    for split, path in paths.items():
        assert digest(path) == audit["source_files_sha256"][path.name]
        with path.open(encoding="utf-8-sig", newline="") as csv_file:
            match[split] = [(i, row) for i, row in enumerate(csv.DictReader(csv_file))
                            if row["Original_id"] == EVENT]
    assert len(match["test"]) == 15 and not match["train"]
    votes = {row["Country"]: row["Voting"] for _, row in match["test"]}
    assert set(votes.values()) == {"Y"}
    assert all(row["Date"] == DATE and ast.literal_eval(row["Authors"]) == ["United Kingdom"]
               for _, row in match["test"])
    draft = base / f"drafts_adopted/{EVENT}/S_2023_808-EN.json"
    assert read(draft)["ID"] == SYMBOL
    meeting = " ".join((pdfs / "meeting.txt").read_text().split())
    vote_match = re.search(r"In favour: (.*?) The President: The draft resolution received 15 votes in favour", meeting)
    assert vote_match and "adopted unanimously as resolution 2704 (2023)" in meeting.replace("\u00a0", " ")
    roll = {country.strip().upper().replace("UNITED KINGDOM OF GREAT BRITAIN AND NORTHERN IRELAND", "UNITED KINGDOM")
            .replace("UNITED STATES OF AMERICA", "UNITED STATES") for country in vote_match[1].split(",")}
    assert set(votes) == roll
    assert all(name in meeting for name in ("as the representative of Brazil", "Agyeman (Ghana)", "Estado Mayor Central"))
    resolution = " ".join((pdfs / "resolution.txt").read_text().split())
    assert all(clause in resolution for clause in ("31 October 2024", "appropriate verification protocols",
                                                    "taking into account an update from the Secretary-General",
                                                    "on the basis of agreement between the parties"))
    checked = {}
    for config in ("adopted", "vetoed"):
        relative = f"{config}/data.parquet"
        source = ROOT / unsc["local_root"] / relative
        assert digest(source) == next(x["sha256"] for x in unsc["files"] if x["path"] == relative)
        fields = (["dates", "identifiers", "draft_from_file1", "meeting"] if config == "adopted"
                  else ["date", "draft_resolution", "meeting_record"])
        rows = pq.read_table(source, columns=fields).to_pylist()
        hits = [i for i, record in enumerate(rows) if
                any(mark in json.dumps(record, ensure_ascii=False) for mark in (SYMBOL, "S/PV.9461", DATE))
                or (record.get("identifiers") or {}).get("res_no") == 2704]
        checked[config] = {"rows": len(rows), "candidate_indices": hits}
    assert not any(row["candidate_indices"] for row in checked.values())
    return {"family": "colombia-verification-renewal-2023-10-30",
            "unbench": {"event": EVENT, "test_rows": [i for i, _ in match["test"]], "train_count": 0,
                        "draft_path": str(draft.relative_to(ROOT)), "draft_sha256": digest(draft),
                        "votes_match_official": votes},
            "unsc_bench": {"revision": unsc["revision"], "configs_checked": checked,
                           "status": "No matching record at the pinned revision. This docket extends coverage with UNBench and the primary UN record."},
            "primary_pdf_sha256": {name: digest(pdfs / f"{name}.pdf") for name in ("meeting", "resolution")},
            "case_sha256": digest(HERE / "case.json")}


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("pdfs", type=Path)
    print(json.dumps(build(cli.parse_args().pdfs), indent=2))
