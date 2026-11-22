"""Verify the request experiment's exact archive join and official roll-call agreement."""
import csv
from hashlib import sha256
import json

import pyarrow.parquet as pq

import facilitator_requested_evidence as experiment
import facilitator_witness_contrast_provenance as archive
from country_persona.unsc_bench import country_name, normalize_record

OFFICIAL_IN_FAVOUR = (
    "Algeria", "China", "Ecuador", "France", "Guyana", "Japan", "Malta", "Mozambique", "Republic of Korea",
    "Sierra Leone", "Slovenia", "Switzerland", "United Kingdom", "United States",
)


def run():
    event = experiment.packet()["event"]
    expected = {country_name(country): "Y" for country in OFFICIAL_IN_FAVOUR}
    expected[country_name("Russian Federation")] = "A"
    root = archive.ROOT
    bundle = json.loads((root / "data/manifests/unbench-full-20260926.json").read_text())
    source = root / bundle["extraction_root"]
    audit = json.loads((root / "reports/eval-pilot-20260926/unbench-audit.json").read_text())
    split = {}
    for name in ("train", "test"):
        file = source / f"task2_{name}_author.csv"
        assert sha256(file.read_bytes()).hexdigest() == audit["source_files_sha256"][file.name]
        with file.open(newline="", encoding="utf-8-sig") as f:
            split[name] = [(i, r) for i, r in enumerate(csv.DictReader(f)) if r["Original_id"] == event["UNBench_event"]]
    assert not split["train"] and len(split["test"]) == len(expected)
    assert {row["Date"] for _, row in split["test"]} == {event["date"]}
    assert {country_name(r["Country"]): r["Voting"] for _, r in split["test"]} == expected

    unsc = json.loads((root / "data/manifests/unsc-bench-20260926.json").read_text())
    matches = []
    for config in ("adopted", "vetoed"):
        relative = f"{config}/data.parquet"
        file = root / unsc["local_root"] / relative
        assert sha256(file.read_bytes()).hexdigest() == next(r["sha256"] for r in unsc["files"]
                                                           if r["path"] == relative)
        for i, data in enumerate(pq.ParquetFile(file).read().to_pylist()):
            row = normalize_record(data, config, i)
            if row["draft_symbol"] == event["draft"] or row["meeting"] == event["meeting"]:
                assert row["date"] == event["date"]
                assert {v["country"]: v["vote"] for v in row["votes"]} == expected
                matches.append({"split": config, "row_index": i})
    return {"event": event, "official_votes": expected,
            "UNBench": {"split": "author_test", "row_indices": [i for i, _ in split["test"]]},
            "UNSC_Bench": {"matches_by_draft_or_meeting": matches, "revision": unsc["revision"]}}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
