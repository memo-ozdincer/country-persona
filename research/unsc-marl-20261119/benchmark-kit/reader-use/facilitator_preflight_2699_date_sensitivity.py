"""Test whether date order alone changed the locked preflight decision."""
import argparse
import json
from pathlib import Path
from unittest.mock import patch

import facilitator_preflight_2699_score as score

study = score.study


def compare(directory):
    rows = study.verify(directory)
    review = json.loads((study.EVIDENCE / "review.json").read_text())
    original = study.field_present

    def either_date_order(text, field):
        parts = field.split()
        reversed_date = len(parts) == 2 and parts[0].isdigit() and parts[1] in ("May", "June", "July")
        return original(text, field) or (reversed_date and original(text, " ".join(parts[::-1])))

    with patch.object(study, "field_present", either_date_order):
        result = score.evaluate(rows, review)
    result["change"] = "Accept month-day as well as day-month for the original date fields. Evaluation grades stay fixed."
    return result


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("directory", type=Path)
    print(json.dumps(compare(cli.parse_args().directory), ensure_ascii=False, indent=2))
