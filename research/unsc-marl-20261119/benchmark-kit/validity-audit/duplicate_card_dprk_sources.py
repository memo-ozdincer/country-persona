"""Join the new DPRK docket to the pinned benchmark releases."""
from hashlib import sha256
import json
from pathlib import Path

import pyarrow.parquet as pq

from country_persona.unsc_bench import normalize_record

ROOT = Path(__file__).resolve().parents[4]
SYMBOL = "S/2024/255"
YES = {"ALGERIA", "ECUADOR", "FRANCE", "GUYANA", "JAPAN", "MALTA", "MOZAMBIQUE",
       "REPUBLIC OF KOREA", "SIERRA LEONE", "SLOVENIA", "SWITZERLAND", "UNITED KINGDOM", "UNITED STATES"}
ROSTER = {**{country: "Y" for country in YES}, "RUSSIAN FEDERATION": "N", "CHINA": "A"}


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def run():
    unbench = json.loads((ROOT / "data/manifests/unbench-full-20260926.json").read_text())
    archive = ROOT / unbench["file"]
    assert digest(archive) == unbench["sha256"]
    source = ROOT / unbench["extraction_root"] / "all_drafts/1936/S_2024_255-EN.json"
    draft = json.loads(source.read_text())
    assert draft["ID"] == SYMBOL and draft["Date"] == "28 March 2024"
    assert all(phrase in draft["Content"] for phrase in ("30 April 2025", "midterm report", "final report"))
    unsc = json.loads((ROOT / "data/manifests/unsc-bench-20260926.json").read_text())
    parquet = ROOT / unsc["local_root"] / "vetoed/data.parquet"
    assert digest(parquet) == next(row["sha256"] for row in unsc["files"] if row["path"] == "vetoed/data.parquet")
    matches = []
    for i, entry in enumerate(pq.read_table(parquet).to_pylist()):
        row = normalize_record(entry, "vetoed", i)
        if row["draft_symbol"] == SYMBOL:
            votes = {item["country"]: item["vote"] for item in row["votes"]}
            assert votes == ROSTER and row["date"] == "2024-03-28" and row["meeting"] == "9591"
            assert not row["issues"]
            matches.append({"zero_based_row": i, "votes": votes})
    assert len(matches) == 1
    return {"draft": SYMBOL, "unbench": {"archive_sha256": unbench["sha256"],
            "path": str(source.relative_to(ROOT)), "sha256": digest(source)},
            "unsc_bench": {"revision": unsc["revision"], "file_sha256": digest(parquet), "vetoed_matches": matches}}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
