"""Exercise candidate-only extraction on the archived Mali and DPRK dockets."""
import argparse
from contextlib import contextmanager
import json
from pathlib import Path
from unittest.mock import patch

import minurso_candidate_fields as extractor
from minurso_atomic_review import digest

ROOT = extractor.first.ROOT
MALI = ROOT / "crossbench/mali/historical-anchors.json"
MALI_KEY = ROOT / "crossbench/mali/historical-task.json"
DPRK = ROOT / "benchmark-kit/evidence/duplicate-card-routes/dprk/scores.json"
DPRK_KEY = ROOT / "benchmark-kit/validity-audit/source-record-dprk-routing.json"
FIELDS = {
    "failure-mechanism": ("What reason does the record give for the failure of S/2023/639?",
                          ("Insufficient votes in favour.", "A permanent-member veto.", "No reason stated.")),
    "speaker-capacity": ("In what capacity does the record say Yamazaki made the statement about Panel operations?",
                         ("As Council President.", "As Japan's national representative.", "No capacity stated.")),
    "sanctions-status": ("What happened to the existing sanctions according to the record?",
                         ("No status stated.", "They expired.", "They remained in force.")),
}
STATUSES = {"failure-mechanism": (1, 2, 0), "speaker-capacity": (2, 1, 0), "sanctions-status": (0, 2, 1)}


def cases():
    mali = json.loads(MALI.read_text())["anchors"][0]["request"]["answer"]
    mali_key = {r["id"]: r["text"] for r in json.loads(MALI_KEY.read_text())["evidence"]}
    assert "1 vote in favour, 1 against and 13 abstentions" in mali_key["status-639"]
    dprk, = [r["raw_record"] for r in json.loads(DPRK.read_text())["four_records"]
             if r["received"] == ["JAPAN", "CHINA"]]
    dprk_key = json.loads(DPRK_KEY.read_text())
    assert "existing sanctions remained in force" in dprk_key["public"]["SCOPE"]
    assert "national capacity as Japan’s representative" in dprk_key["cards"]["JAPAN"]["text"]
    records = [
        ("mali", "failure-mechanism", mali, "for insufficient affirmative votes", "because a permanent member vetoed it", ""),
        ("dprk", "speaker-capacity", dprk,
         "Council President Yamazaki, speaking as Japan's representative,",
         "Yamazaki, speaking in his capacity as Council President,",
         "Yamazaki"),
        ("dprk", "sanctions-status", dprk, "; existing sanctions (SCOPE) remain active",
         "; existing sanctions (SCOPE) expired", ""),
    ]
    for docket, field, record, original, wrong, missing in records:
        assert record.count(original) == 1
        yield f"{docket}/{field}/original", record, field, 1
        yield f"{docket}/{field}/reversed", record.replace(original, wrong), field, 2
        yield f"{docket}/{field}/omitted", record.replace(original, missing).replace(" .", "."), field, 0


def hashes():
    files = [Path(__file__).resolve(), MALI, MALI_KEY, DPRK, DPRK_KEY]
    return {**BASE_HASHES(), **{str(p.relative_to(ROOT)): digest(p) for p in files}}


BASE_HASHES = extractor.hashes


@contextmanager
def parameters():
    with patch.object(extractor.controls, "cases", cases), patch.multiple(
        extractor, FIELDS=FIELDS, STATUSES=STATUSES, hashes=hashes
    ):
        yield


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("mode", choices=("run", "report"))
    cli.add_argument("directory", type=Path)
    cli.add_argument("--model", type=Path)
    args = cli.parse_args()
    with parameters():
        if args.mode == "run":
            if not args.model:
                cli.error("run requires --model")
            extractor.run(args.model, args.directory)
        else:
            result = extractor.report(args.directory)
            result["scope"] = ("New to this extraction test and previously exposed in the project. "
                               "Two source dossiers, three archived record-field pairs, and six authored changes. "
                               "The same extraction-only instructions and order-agreement rule are used.")
            print(json.dumps(result, ensure_ascii=False, indent=2))
