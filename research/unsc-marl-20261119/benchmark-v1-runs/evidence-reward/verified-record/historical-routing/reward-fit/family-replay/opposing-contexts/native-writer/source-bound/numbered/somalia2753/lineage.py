"""Join the official docket to the locally pinned UNBench and UNSC-Bench releases."""
from hashlib import sha256
import json
from pathlib import Path
import subprocess

import pyarrow.parquet as pq

ROOT = Path(subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip())
UN = ROOT / "data/raw/unbench-audit-20260926/full/UNBench-all"
SC = ROOT / "data/raw/unsc-bench-audit-20260926"


def run():
    meeting = UN / "meetings_adopted/2554/S_PV.9764-EN.json"
    utterances = meeting.with_name("S_PV.9764-EN_statements.json")
    draft = UN / "drafts_adopted/2554/S_2024_790-EN.json"
    adopted = SC / "adopted/data.parquet"
    release = json.loads((SC / "acquisition.json").read_text())
    digest = sha256(adopted.read_bytes()).hexdigest()
    assert digest == next(r["sha256"] for r in release["files"] if r["path"] == "adopted/data.parquet")
    table = pq.read_table(adopted, columns=["identifiers", "draft_from_file1", "meeting", "voting_totals"])
    votes = []
    for row in table.to_pylist():
        details = row["identifiers"]
        draft_row = row["draft_from_file1"]
        symbol = str(details["symbol"] or "").replace(" ", "")
        draft_symbol = draft_row["draft_symbol"] if draft_row else None
        meeting_text = str(row["meeting"])
        if ("S/RES/2753" in symbol or draft_symbol == "S/2024/790"
                or any(key in meeting_text for key in ("S/PV.9764", "S_PV.9764"))):
            votes.append({"symbol": symbol, "draft_symbol": draft_symbol, "meeting": row["meeting"],
                          "voting_totals": row["voting_totals"]})
    assert len(votes) <= 1
    report, instrument = (json.loads(path.read_text()) for path in (meeting, draft))
    assert "resolution 2753 (2024)" in report["Content"] and instrument["ID"] == "S/2024/790"
    return {"benchmarks": {"UNBench": {"join_directory": "2554", "draft_id": instrument["ID"],
                                         "authors": instrument["Authors"], "meeting": "S/PV.9764",
                                         "resolution": "2753 (2024)"},
                           "UNSC-Bench": {"revision": release["revision"], "adopted_rows_checked": table.num_rows, "matches": votes}},
            "inputs_sha256": {str(path.relative_to(ROOT)): sha256(path.read_bytes()).hexdigest()
                              for path in (meeting, utterances, draft)} | {str(adopted.relative_to(ROOT)): digest}}


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, indent=2))
