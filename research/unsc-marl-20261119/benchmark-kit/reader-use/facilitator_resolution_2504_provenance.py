"""Verify the fresh case against the official roll call and both benchmark releases."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
from unittest.mock import patch

import facilitator_emergency_session_provenance as provenance
import facilitator_resolution_2719_score as prior

HERE = prior.study.HERE
EVIDENCE = HERE / "facilitator-resolution-2504-evidence"
PACKET = EVIDENCE / "packet.json"


def packet():
    return json.loads(PACKET.read_text())


def run():
    names = {
        "Y": ("Belgium", "Dominican Republic", "Estonia", "France", "Germany", "Indonesia", "Niger",
              "Saint Vincent and the Grenadines", "South Africa", "Tunisia", "Viet Nam"),
        "A": ("China", "Russian Federation", "United Kingdom", "United States"),
    }
    official = {provenance.country_name(name): vote for vote, group in names.items() for name in group}
    with patch.object(provenance.study, "packet", packet), patch.object(provenance, "OFFICIAL", official):
        data = provenance.audit_for_votes()
    assert data["UNSC_Bench"]["matches_by_draft_or_meeting"] == [{"split": "adopted", "row_index": 245}]
    points = prior.ceilings(packet()["criteria"])
    assert points == [42, 46, 48, 52, 50, 59, 61, 70]
    return {"roll_call": data, "authored_receipt_ceilings": points, "packet_sha256": sha256(PACKET.read_bytes()).hexdigest()}


if __name__ == "__main__":
    argparse.ArgumentParser(description=__doc__).parse_args()
    print(json.dumps(run(), indent=2))
