"""Audit the Gulf of Guinea and Libya joins against the pinned benchmark releases."""
import csv
from hashlib import sha256
import json
from pathlib import Path

import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[4]


def load(path):
    return json.loads(path.read_text())


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def audit():
    unbench = load(ROOT / "data/manifests/unbench-full-20260926.json")
    unsc = load(ROOT / "data/manifests/unsc-bench-20260926.json")
    checks = load(ROOT / "reports/eval-pilot-20260926/unbench-audit.json")["source_files_sha256"]
    author = ROOT / unbench["extraction_root"]
    unbench_event = "2438"
    path = author / "drafts_adopted" / unbench_event / "S_2022_62-EN.json"
    draft_record = load(path)
    assert draft_record["ID"] == "22-08235" and draft_record["Date"] == "31 May 2022"
    assert "Gulf of Guinea" in draft_record["Title"]
    author_splits = {}
    for split in ("train", "test"):
        vote_path = author / f"task2_{split}_author.csv"
        assert digest(vote_path) == checks[vote_path.name]
        with vote_path.open(encoding="utf-8-sig", newline="") as f:
            votes = [(n, row) for n, row in enumerate(csv.DictReader(f)) if row["Original_id"] == unbench_event]
        author_splits[split] = votes
    votes = author_splits["test"]
    assert not author_splits["train"] and len(votes) == 15
    assert {r["Date"] for _, r in votes} == {"2022-05-31"}
    assert {r["Voting"] for _, r in votes} == {"Y"}
    assert {"CHINA", "GHANA"} <= {r["Country"] for _, r in votes}

    matches = {}
    targets = {"guinea": ("9050", "2634", "S/2022/62"), "libya": ("10029", "2796", "S/2025/691")}
    for name in ("adopted", "vetoed"):
        relative = f"{name}/data.parquet"
        parquet = ROOT / unsc["local_root"] / relative
        assert digest(parquet) == next(item["sha256"] for item in unsc["files"] if item["path"] == relative)
        p = pq.ParquetFile(parquet)
        cols = [key for key in ("identifiers", "meeting", "draft_from_file1", "draft_resolution", "meeting_record") if key in p.schema_arrow.names]
        rows = p.read(columns=cols).to_pylist()
        matches[name] = {"rows": len(rows)}
        for family, (meeting, resolution, draft) in targets.items():
            hits = []
            for i, row in enumerate(rows):
                ids = row.get("identifiers") or {}
                m = row.get("meeting") or {}
                d = row.get("draft_from_file1") or {}
                if (str(ids.get("res_no")) == resolution or str(m.get("meeting_no")) == meeting
                        or m.get("meeting_record") == f"S/PV.{meeting}" or d.get("draft_symbol") == draft
                        or str(row.get("meeting_record")).removeprefix("S/PV.") == meeting
                        or row.get("draft_resolution") == draft):
                    hits.append(i)
            matches[name][family] = hits
    return {"unbench": {"guinea": {"event": unbench_event, "draft": str(path.relative_to(ROOT)),
                                  "draft_sha256": digest(path), "task2_split": "test",
                                  "task2_zero_based_rows": [n for n, _ in votes],
                                  "country_votes": {r["Country"]: r["Voting"] for _, r in votes}},
                        "libya": "Official record extension. No UNBench row used."},
            "unsc_bench": {"revision": unsc["revision"], "matches": matches}}


if __name__ == "__main__":
    print(json.dumps(audit(), indent=2))
