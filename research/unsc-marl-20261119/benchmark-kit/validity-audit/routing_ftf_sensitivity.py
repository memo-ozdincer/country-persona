"""Audit release and scope sensitivity on frozen written-ballot records."""
import argparse
from copy import deepcopy
import json
from pathlib import Path
from tempfile import TemporaryDirectory

import routing_ftf_independence as baseline
import routing_ftf_record as record


def evaluate(directory):
    standard = record.read(directory / "annotations.json")
    rows = {}
    with TemporaryDirectory() as scratch:
        for name, relax_guard, relax_scope in (
            ("release_uncertain", True, False),
            ("origin_only_credit", False, True),
            ("both", True, True),
        ):
            altered = deepcopy(standard)
            if relax_guard:
                for row in altered["rows"].values():
                    if row["guard"] == "uncertain":
                        row["guard"] = "clear"
            if relax_scope:
                for key in ("receipt-1", "receipt-5"):
                    altered["rows"][key]["met"]["us"] = altered["rows"][key]["issues"]["us"]
            path = Path(scratch) / "annotations.json"
            path.write_text(json.dumps(altered))
            scores = record.score(directory, directory / "plan.json", path)
            assessed = Path(scratch) / "scores.json"
            assessed.write_text(json.dumps(scores))
            fair = baseline.score(assessed, directory / "independent-plan.json")["outcomes"]
            rows[name] = {
                "raw_vector": scores["raw_vector"], "eligible_vector": scores["eligible_vector"],
                "raw_matched_gains": {k: v["team_minus_independent"] for k, v in fair["raw"].items()},
                "released_matched_gains": {k: v["team_minus_independent"] for k, v in fair["release"].items()},
            }
    return {"scope": "Post-review sensitivity. Policies, texts and source access remain fixed. Relax the two "
                     "uncertain guards, credit 'countries of origin' without the nationality alternative in the "
                     "two records that say so, or apply both changes. Confirmed guard failures remain in place.",
            "annotations_sha256": record.digest(directory / "annotations.json"), "outcomes": rows}


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("directory", type=Path)
    print(json.dumps(evaluate(cli.parse_args().directory), indent=2))
