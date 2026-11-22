"""Build an arm-free deck and replay source scoring for the Sudan chairs."""
import argparse
import json
from pathlib import Path
from unittest.mock import patch

import source_record_review as review
import source_record_sudan_chair_control as control
from source_record_sudan import CASE


class Packet:
    def read_text(self):
        case = json.loads(CASE.read_text())
        return json.dumps({"cases": [{**case, "family": "sudan-chair-control"}]})


def read(directory, annotation=None):
    with patch.object(review, "PACK", Packet()):
        if annotation is None:
            return review.bundle(directory)[0]
        scores = review.score(directory, annotation)
        _, join = review.bundle(directory)
    stats = control.replay(directory)
    for key, identifier in join.items():
        row = scores[identifier]
        row.update(stats["stats"][identifier])
        row["release_eligible"] = row["critical_guard"] == "clear" and row["under_limit"] and row["ended"]
        row["eligible_floor"] = row["floor"] if row["release_eligible"] else 0
        row["eligible_ceiling"] = row["ceiling"] if row["release_eligible"] else 0
        row["access_status"] = annotation["reviews"][key]["units"]["A2"][0]
    contrasts = {}
    for order in control.ORDERS:
        arms = {arm: scores[f"sudan-chair-control/{order}/{arm}"] for arm in control.ARMS}
        contrasts[order] = {
            comparison: {
                "raw_interval": [arms["interactive"]["floor"] - arms[comparison]["ceiling"],
                                 arms["interactive"]["ceiling"] - arms[comparison]["floor"]],
                "eligible_interval": [arms["interactive"]["eligible_floor"] - arms[comparison]["eligible_ceiling"],
                                      arms["interactive"]["eligible_ceiling"] - arms[comparison]["eligible_floor"]],
            } for comparison in ("independent_drafts", "draft_free")
        }
    plans = control.requests()
    source = json.loads(plans[0]["messages"][1]["content"])["evidence"]["TEXT"]
    assert "facilitating humanitarian access" in source
    rows = control.archived_rows()
    revisions = {
        f"{arm}/revision_{index}": rows[f"{arm}/revision_{index}"]["output"]
        for arm in control.ARMS[:2] for index in (1, 2)
    }
    assert all("access" not in content.lower() for content in revisions.values())
    return {"scope": annotation["scope"], "same_output_as_archived": stats["same_output_as_archived"],
            "final": scores, "paired_effects": contrasts,
            "access_provenance": {"shared_chair_block": "TEXT", "support": source,
                                  "delivered_revisions": revisions}}


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("directory", type=Path)
    cli.add_argument("--annotations", type=Path)
    args = cli.parse_args()
    annotations = json.loads(args.annotations.read_text()) if args.annotations else None
    print(json.dumps(read(args.directory, annotations), indent=2, ensure_ascii=False))
