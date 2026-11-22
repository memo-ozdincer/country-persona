"""Join two release-backed development cases to primary UN vote checks."""
import csv
import hashlib
import json
from pathlib import Path
import sys

import pyarrow.parquet as pq

from country_persona.action_eval import classification_metrics
from country_persona.unsc_bench import normalize_record

ROOT = Path(__file__).resolve().parents[3]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build():
    unbench = json.loads((ROOT / "data/manifests/unbench-full-20260926.json").read_text())
    ub_root = ROOT / unbench["extraction_root"]
    ub_csv = ub_root / "task2_test_author.csv"
    ub_audit = json.loads((ROOT / "reports/eval-pilot-20260926/unbench-audit.json").read_text())
    assert sha(ub_csv) == ub_audit["source_files_sha256"][ub_csv.name]
    ub_draft = ub_root / "drafts_adopted/2467/S_2022_925-EN.json"
    assert json.loads(ub_draft.read_text())["ID"] == "S/2022/925"
    with ub_csv.open(newline="", encoding="utf-8-sig") as data:
        selected = [(i, r) for i, r in enumerate(csv.DictReader(data)) if r["Original_id"] == "2467"]
    assert len(selected) == 15 and all(r["Date"] == "2022-12-09" for _, r in selected)
    ub_votes = {r["Country"]: r["Voting"] for _, r in selected}
    assert len(ub_votes) == 15 and ub_votes["INDIA"] == "A" and ub_votes["BRAZIL"] == "Y"
    assert sum(vote == "Y" for vote in ub_votes.values()) == 14

    unsc = json.loads((ROOT / "data/manifests/unsc-bench-20260926.json").read_text())
    file = "vetoed/data.parquet"
    source = ROOT / unsc["local_root"] / file
    assert sha(source) == next(f["sha256"] for f in unsc["files"] if f["path"] == file)
    ws = normalize_record(pq.read_table(source).slice(11, 1).to_pylist()[0], "vetoed", 11)
    assert not ws["issues"] and ws["draft_symbol"] == "S/2023/970" and ws["date"] == "2023-12-08"
    ws_votes = {r["country"]: r["vote"] for r in ws["votes"]}
    assert (ws_votes["FRANCE"], ws_votes["UNITED KINGDOM"], ws_votes["BRAZIL"]) == ("Y", "A", "Y")
    assert len(ws_votes) == 15 and sum(v == "Y" for v in ws_votes.values()) == 13
    assert ws_votes["UNITED STATES"] == "N" and "INDIA" not in ws_votes

    rows = [
        {"family": "sanctions", "draft": "S/2022/925", "meeting": "S/PV.9214", "date": "2022-12-09",
         "benchmark": "UNBench Task 2 author test", "release_sha256": unbench["sha256"],
         "original_id": "2467", "vote_row_indexes": [i for i, _ in selected], "draft_file_sha256": sha(ub_draft),
         "primary_vote_record": "https://digitallibrary.un.org/record/3997276", "votes": ub_votes},
        {"family": "gaza", "draft": ws["draft_symbol"], "meeting": "S/PV.9499", "date": ws["date"],
         "benchmark": "UNSC-Bench vetoed", "revision": unsc["revision"], "row_index": 11,
         "source_file_sha256": sha(source), "primary_vote_record": "https://docs.un.org/en/S/PV.9499",
         "votes": ws_votes},
    ]
    return {
        "scope": "Previously exposed development rows. Keep vote references out of prediction prompts.",
        "rows": rows,
        "always_yes": {r["family"]: classification_metrics(list(r["votes"].values()), ["Y"] * 15) for r in rows},
    }


if __name__ == "__main__":
    with Path(sys.argv[1]).open("x") as output:
        json.dump(build(), output, indent=2)
        output.write("\n")
