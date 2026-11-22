"""Verify release membership and flag the MINURSO primary-vote disagreement."""
import argparse
import csv
from hashlib import sha256
import json
from pathlib import Path

from source_record_minurso import PACK

ROOT = PACK.resolve().parents[4]
PRIMARY = {
    "meeting": {
        2: ("document S/2024/796", "S/2024/797"),
        3: ("6 votes in favour, none against and 9 abstentions",
            "5 votes in favour, none against and 10 abstentions",
            "12 votes in favour, none against and 2 abstentions",
            "One member did not participate in the voting."),
        7: ("Algeria made the fully conscious and responsible decision not to participate",
            "they were deliberately ignored"),
        9: ("That is why Switzerland supported amendment S/2024/797",
            "we abstained in the voting on the amendment in order to ensure the continuity of MINURSO’s work",
            "I now resume my functions as President of the Council."),
    },
    "resolution": {
        3: ("Decides to extend the mandate of MINURSO until 31 October 2025",
            "including through facilitating visits to the region"),
    },
}


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def verify_pdf(kind, path, expected):
    import pymupdf

    checksum = digest(path)
    assert checksum == expected
    with pymupdf.open(path) as document:
        for page, phrases in PRIMARY[kind].items():
            text = " ".join(document[page - 1].get_text().split())
            assert all(phrase in text for phrase in phrases), (kind, page)
        return {"sha256": checksum, "pages": len(document),
                "source_checks_by_page": {str(page): len(v) for page, v in PRIMARY[kind].items()}}


def verify_releases():
    import pyarrow.parquet as pq
    from country_persona.unsc_bench import normalize_record

    release = json.loads(PACK.read_text())["release"]
    raw = ROOT / "data/manifests"
    unbench = json.loads((raw / "unbench-full-20260926.json").read_text())
    ub_root = ROOT / unbench["extraction_root"]
    draft_ids = {}
    for path, checksum in release["unbench_archive_entries"].items():
        file = ub_root / path
        assert digest(file) == checksum
        draft_ids[path] = json.loads(file.read_text())["ID"]
    assert set(draft_ids.values()) == {"S/2024/796", "S/2024/797", "S/2024/798"}
    with (ub_root / "task2_test_author.csv").open(encoding="utf-8-sig") as handle:
        test_rows = sum(row["Original_id"] == "1970" for row in csv.DictReader(handle))
    assert not test_rows

    reference = release["unsc_bench"]
    unsc = json.loads((raw / "unsc-bench-20260926.json").read_text())
    assert reference["revision"] == unsc["revision"]
    config, index = (reference[key] for key in ("config", "index"))
    relative = f"{config}/data.parquet"
    parquet = ROOT / unsc["local_root"] / relative
    checksum = digest(parquet)
    assert checksum == next(x["sha256"] for x in unsc["files"] if x["path"] == relative)
    record = pq.read_table(parquet).slice(index, 1).to_pylist()[0]
    normal = normalize_record(record, config, index)
    assert normal["draft_symbol"] == "S/2024/796" and normal["date"] == "2024-10-31"
    assert record["meeting"]["meeting_record"] == "S/PV.9771"
    assert "Algeria did not participate" in record["content"]["notes"]
    votes = {row["country"]: row["vote"] for row in normal["votes"]}
    assert [c for c, v in votes.items() if v == "A"] == ["ALGERIA", "MOZAMBIQUE", "RUSSIAN FEDERATION"]
    assert list(votes.values()).count("Y") == 12 and len(votes) == 15
    return {
        "UNBench": {"draft_ids": draft_ids, "main_draft_author_vote_test_rows": test_rows},
        "UNSC-Bench": {"config": config, "index": index, "parquet_sha256": checksum,
                       "normalized_vote": votes["ALGERIA"], "note_confirms_non_participation": True},
        "primary_algeria_final_vote": reference["algeria_primary"],
        "historical_prediction": "No prediction was run. Use a distinct non-participation label or flag the discrepancy for vote evaluation.",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("meeting", type=Path)
    parser.add_argument("resolution", type=Path)
    args = parser.parse_args()
    refs = json.loads(PACK.read_text())["release"]
    results = {"primary": {kind: verify_pdf(kind, getattr(args, kind), refs[f"{kind}_sha256"]) for kind in PRIMARY},
               "archives": verify_releases()}
    print(json.dumps(results, indent=2))
