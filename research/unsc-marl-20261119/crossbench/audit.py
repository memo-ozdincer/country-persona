"""Bind two new evaluation families to pinned releases and audit workshop conditions."""
import argparse
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path

import pyarrow.parquet as pq

from country_persona.unsc_bench import normalize_record

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def read(relative):
    return json.loads((ROOT / relative).read_text())


def digest(path):
    hasher = hashlib.sha256()
    with path.open("rb") as raw:
        for chunk in iter(lambda: raw.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def build():
    ub = read("data/manifests/unbench-full-20260926.json")
    uc = read("data/manifests/unsc-bench-20260926.json")
    report = read("reports/eval-pilot-20260926/unbench-audit.json")
    archive = ROOT / ub["file"]
    assert digest(archive) == ub["sha256"]
    author_root = ROOT / ub["extraction_root"]
    vote_files = {split: author_root / f"task2_{split}_author.csv" for split in ("train", "test")}
    found = {}
    for split, path in vote_files.items():
        assert digest(path) == report["source_files_sha256"][path.name]
        with path.open(encoding="utf-8-sig", newline="") as source:
            found[split] = [(i, r) for i, r in enumerate(csv.DictReader(source)) if r["Original_id"] == "2484"]
    assert not found["train"] and len(found["test"]) == 15
    test = found["test"]
    assert {r["Date"] for _, r in test} == {"2023-05-30"}
    iraq_votes = {r["Country"]: r["Voting"] for _, r in test}
    assert len(iraq_votes) == 15 and set(iraq_votes.values()) == {"Y"}

    def unsc_row(config, index):
        relative = f"{config}/data.parquet"
        path = ROOT / uc["local_root"] / relative
        assert digest(path) == next(r["sha256"] for r in uc["files"] if r["path"] == relative)
        row = pq.read_table(path).slice(index, 1).to_pylist()[0]
        record = normalize_record(row, config, index)
        assert not record["issues"]
        return record

    iraq, syria = unsc_row("adopted", 256), unsc_row("vetoed", 15)
    assert iraq["draft_symbol"] == "S/2023/378" and iraq["meeting"] == "S/PV.9331"
    assert iraq["date"] == "2023-05-30" and {r["country"]: r["vote"] for r in iraq["votes"]} == iraq_votes
    assert syria["draft_symbol"] == "S/2023/506" and syria["date"] == "2023-07-11"
    assert str(syria["meeting"]).removeprefix("S/PV.") == "9371"
    syria_votes = {r["country"]: r["vote"] for r in syria["votes"]}
    assert Counter(syria_votes.values()) == Counter(Y=13, N=1, A=1)
    assert {k: syria_votes[k] for k in ("BRAZIL", "UNITED KINGDOM", "RUSSIAN FEDERATION", "CHINA")} == {
        "BRAZIL": "Y", "UNITED KINGDOM": "Y", "RUSSIAN FEDERATION": "N", "CHINA": "A",
    }
    unbench_drafts = [author_root / name for name in (
        "drafts_adopted/2484/S_2023_378-EN.json", "all_drafts/1889/S_2023_506-EN.json")]
    assert [json.loads(p.read_text())["ID"] for p in unbench_drafts] == ["S/2023/378", "S/2023/506"]
    workshops = json.loads((HERE / "workshops.json").read_text())
    result = {}
    for item, draft, source in zip(workshops["families"], unbench_drafts, (iraq, syria), strict=True):
        assert item["draft"] == source["draft_symbol"]
        assert item["date"] == source["date"]
        options = item["packages"]
        assert {o["id"] for o in options} == {"A", "B", "C", "D"} and len(options) == 4
        variants = {}
        for variant in item["variants"]:
            roles = variant["private_conditions"]
            assert len(roles) == 2 and all(r for r in roles)
            accepted = [{o["id"] for o in options if all(o.get(k) == v for k, v in role.items())} for role in roles]
            overlap = accepted[0] & accepted[1]
            assert all(len(a) == 2 for a in accepted)
            assert len(overlap) == int(variant["id"] == "overlap")
            variants[variant["id"]] = {"allowed_by_role": [sorted(s) for s in accepted],
                                      "joint_packages": sorted(overlap), "truth": "agreement_possible" if overlap else "impasse"}
        result[item["id"]] = {
            "benchmark": {"unbench_draft_path": str(draft.relative_to(ROOT)), "unbench_draft_sha256": digest(draft),
                          "unbench_task2_test_rows": [i for i, _ in test] if source is iraq else [],
                          "unsc_bench_config": source["config"], "unsc_bench_index": source["row_index"],
                          "unsc_bench_revision": uc["revision"]},
            "prediction_ref_only": {r["country"]: r["vote"] for r in source["votes"]},
            "workshop_refs_only": variants,
        }
    return {
        "scope": "Development evaluation. Reference-only labels. Existing public cases may be in model pretraining.",
        "workshop_file_sha256": digest(HERE / "workshops.json"),
        "families": result,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    with args.output.open("x") as out:
        json.dump(build(), out, indent=2, ensure_ascii=False)
        out.write("\n")
