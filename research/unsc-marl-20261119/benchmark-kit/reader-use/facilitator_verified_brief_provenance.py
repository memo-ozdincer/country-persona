"""Join the transferred brief packet to the pinned author splits and roll calls."""
import csv
from hashlib import sha256
import json
from pathlib import Path
from unittest.mock import patch

import pyarrow.parquet as pq

import facilitator_witness_contrast_provenance as provenance
from country_persona.unsc_bench import country_name, normalize_record

HERE = Path(__file__).resolve().parent
PACK = HERE / "facilitator_verified_brief-packet.json"
AUDIT = provenance.ROOT / "reports/eval-pilot-20260926/unbench-audit.json"
# Named voting categories from the two Digital Library roll calls.
OFFICIAL = {
    "gaza-2728": ("2024-03-25", "2529", {
        "Y": "Algeria,China,Ecuador,France,Guyana,Japan,Malta,Mozambique,Republic of Korea,Russian Federation,Sierra Leone,Slovenia,Switzerland,United Kingdom",
        "A": "United States",
    }),
    "myanmar-2669": ("2022-12-21", "2472", {
        "Y": "Albania,Brazil,France,Gabon,Ghana,Ireland,Kenya,Mexico,Norway,United Arab Emirates,United Kingdom,United States",
        "A": "China,India,Russian Federation",
    }),
}


def report():
    with patch.object(provenance, "PACK", PACK):
        result = provenance.report()
    pack = json.loads(PACK.read_text())
    manifest = json.loads((provenance.ROOT / "data/manifests/unbench-full-20260926.json").read_text())
    checked = json.loads(AUDIT.read_text())["source_files_sha256"]
    author = provenance.ROOT / manifest["extraction_root"]
    datasets = {}
    for split in ("train", "test"):
        source = author / f"task2_{split}_author.csv"
        assert sha256(source.read_bytes()).hexdigest() == checked[source.name]
        with source.open(encoding="utf-8-sig", newline="") as f:
            datasets[split] = list(csv.DictReader(f))

    unsc = json.loads((provenance.ROOT / "data/manifests/unsc-bench-20260926.json").read_text())
    parquet = pq.ParquetFile(provenance.ROOT / unsc["local_root"] / "adopted/data.parquet").read()
    for family, (date, code, codes) in OFFICIAL.items():
        expected = {country_name(name): vote for vote, group in codes.items() for name in group.split(",")}
        assert len(expected) == 15
        assert not [r for r in datasets["train"] if r["Original_id"] == code]
        rows = [(i, r) for i, r in enumerate(datasets["test"]) if r["Original_id"] == code]
        assert len(rows) == 15 and {r["Date"] for _, r in rows} == {date}
        assert {country_name(r["Country"]): r["Voting"] for _, r in rows} == expected
        join = result["joins"][family]
        join["UNBench_task2"] = {"event": code, "split": "author_test", "row_indices": [i for i, _ in rows],
                                 "votes_matching_official": len(rows), "official_rollcall": pack[family]["roll_call"]}
        for candidate in join["UNSC_Bench"]:
            index = candidate["row_index"]
            assert candidate["config"] == "adopted" and candidate["date"] == date
            row = normalize_record(parquet.slice(index, 1).to_pylist()[0], "adopted", index)
            assert {v["country"]: v["vote"] for v in row["votes"]} == expected
            candidate["votes_matching_official"] = len(expected)
    return result


if __name__ == "__main__":
    print(json.dumps(report(), indent=2))
