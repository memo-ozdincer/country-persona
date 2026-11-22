"""Join the Sudan docket to pinned UNBench and UNSC-Bench releases."""
from collections import Counter
import csv
from hashlib import sha256
import json
from pathlib import Path

import pyarrow.parquet as pq
from country_persona.unsc_bench import normalize_record

ROOT = Path(__file__).resolve().parents[3]
SYMBOL, DATE, MEETING = "S/2024/826", "2024-11-18", "S/PV.9786"
IDENTIFIER = "1975"


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def build():
    unbench = json.loads((ROOT / "data/manifests/unbench-full-20260926.json").read_text())
    archive = ROOT / unbench["file"]
    assert digest(archive) == unbench["sha256"]
    extracted = ROOT / unbench["extraction_root"]
    draft = extracted / "all_drafts" / IDENTIFIER / "S_2024_826-EN.json"
    assert json.loads(draft.read_text())["ID"] == SYMBOL
    audit = json.loads((ROOT / "reports/eval-pilot-20260926/unbench-audit.json").read_text())
    vote_csv = {}
    for split in ("train", "test"):
        path = extracted / f"task2_{split}_author.csv"
        checksum = digest(path)
        assert checksum == audit["source_files_sha256"][path.name]
        with path.open(encoding="utf-8-sig", newline="") as stream:
            matches = Counter(row["Date"] for row in csv.DictReader(stream) if row["Original_id"] == IDENTIFIER)
        vote_csv[split] = {"sha256": checksum, "id_match_dates": dict(matches),
                           "same_id_and_date": matches[DATE]}

    unsc = json.loads((ROOT / "data/manifests/unsc-bench-20260926.json").read_text())
    config = "vetoed"
    relative = f"{config}/data.parquet"
    path = ROOT / unsc["local_root"] / relative
    checksum = digest(path)
    assert checksum == next(item["sha256"] for item in unsc["files"] if item["path"] == relative)
    rows = [normalize_record(row, config, i) for i, row in enumerate(pq.read_table(path).to_pylist())]
    row, = [(i, item) for i, item in enumerate(rows) if item["draft_symbol"] == SYMBOL]
    index, item = row
    votes = {entry["country"]: entry["vote"] for entry in item["votes"]}
    support = ("ALGERIA|CHINA|ECUADOR|FRANCE|GUYANA|JAPAN|MALTA|MOZAMBIQUE|REPUBLIC OF KOREA|"
               "SIERRA LEONE|SLOVENIA|SWITZERLAND|UNITED KINGDOM|UNITED STATES")
    assert not item["issues"] and item["date"] == DATE and str(item["meeting"]).removeprefix("S/PV.") == "9786"
    assert votes == {**dict.fromkeys(support.split("|"), "Y"), "RUSSIAN FEDERATION": "N"}
    return {
        "scope": "Dated draft and roll-call linkage. The retrospective outcomes are reference evidence.",
        "family": "sudan-civilian-protection-2024-11-18", "draft": SYMBOL, "date": DATE, "meeting": MEETING,
        "unbench": {"archive_sha256": unbench["sha256"], "draft_path": str(draft.relative_to(extracted)),
                    "draft_sha256": digest(draft), "author_vote_csv": vote_csv},
        "unsc_bench": {"revision": unsc["revision"], "config": config, "row_index": index, "sha256": checksum},
        "verified_roll_call": votes,
        "primary": {
            "draft": "https://digitallibrary.un.org/record/4066685",
            "meeting": "https://digitallibrary.un.org/record/4066876",
            "special_report": "https://www.un.org/pga/wp-content/uploads/sites/109/2024/11/241121-PSC-letter-to-PGA-Special-Rpt-UNSC-9786th-mtg-SIGNED57.pdf",
        },
    }


if __name__ == "__main__":
    print(json.dumps(build(), indent=2))
