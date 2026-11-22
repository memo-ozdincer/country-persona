"""Join both benchmark releases to the official Resolution 2623 roll call."""
import json

from country_persona.unsc_bench import country_name
import facilitator_requested_evidence_provenance as audit
import facilitator_emergency_session as study

YES = ("Albania", "Brazil", "France", "Gabon", "Ghana", "Ireland", "Kenya", "Mexico", "Norway",
       "United Kingdom", "United States")
OFFICIAL = {country_name(name): "Y" for name in YES} | {
    country_name("Russian Federation"): "N", country_name("China"): "A", country_name("India"): "A",
    country_name("United Arab Emirates"): "A",
}


def report():
    result = audit_for_votes()
    assert result["UNSC_Bench"]["matches_by_draft_or_meeting"] == [{"split": "adopted", "row_index": 248}]
    return result


def audit_for_votes():
    import csv
    from hashlib import sha256

    import pyarrow.parquet as pq

    event = study.packet()["event"]
    root = audit.archive.ROOT
    unbench = json.loads((root / "data/manifests/unbench-full-20260926.json").read_text())
    hashes = json.loads((root / "reports/eval-pilot-20260926/unbench-audit.json").read_text())["source_files_sha256"]
    rows = {}
    for split in ("train", "test"):
        file = root / unbench["extraction_root"] / f"task2_{split}_author.csv"
        assert sha256(file.read_bytes()).hexdigest() == hashes[file.name]
        with file.open(newline="", encoding="utf-8-sig") as f:
            rows[split] = [(i, row) for i, row in enumerate(csv.DictReader(f)) if row["Original_id"] == event["UNBench_event"]]
    assert not rows["train"] and len(rows["test"]) == 15
    assert {r["Date"] for _, r in rows["test"]} == {event["date"]}
    assert {country_name(r["Country"]): r["Voting"] for _, r in rows["test"]} == OFFICIAL
    unsc = json.loads((root / "data/manifests/unsc-bench-20260926.json").read_text())
    file = root / unsc["local_root"] / "adopted/data.parquet"
    assert sha256(file.read_bytes()).hexdigest() == next(x["sha256"] for x in unsc["files"] if x["path"] == "adopted/data.parquet")
    found = []
    for i, raw in enumerate(pq.ParquetFile(file).read().to_pylist()):
        row = audit.normalize_record(raw, "adopted", i)
        if row["meeting"] == event["meeting"] or row["draft_symbol"] == event["draft"]:
            assert row["meeting"] == event["meeting"] and row["draft_symbol"] == event["draft"] and row["date"] == event["date"]
            assert {v["country"]: v["vote"] for v in row["votes"]} == OFFICIAL
            found.append({"split": "adopted", "row_index": i})
    return {"event": event, "official_votes": OFFICIAL,
            "UNBench": {"split": "author_test", "row_indices": [i for i, _ in rows["test"]]},
            "UNSC_Bench": {"matches_by_draft_or_meeting": found, "revision": unsc["revision"]}}


if __name__ == "__main__":
    print(json.dumps(report(), indent=2))
