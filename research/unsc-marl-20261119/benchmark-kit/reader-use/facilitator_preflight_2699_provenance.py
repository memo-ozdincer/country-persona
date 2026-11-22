"""Join both benchmark releases to the official Resolution 2699 votes."""
import json
from unittest.mock import patch

import facilitator_emergency_session_provenance as audit
import facilitator_preflight_2699 as study


def run():
    yes = ("Albania", "Brazil", "Ecuador", "France", "Gabon", "Ghana", "Japan", "Malta", "Mozambique",
           "Switzerland", "United Arab Emirates", "United Kingdom", "United States")
    votes = {audit.country_name(name): "Y" for name in yes}
    votes.update({audit.country_name(name): "A" for name in ("China", "Russian Federation")})
    with patch.object(audit.study, "packet", study.packet), patch.object(audit, "OFFICIAL", votes):
        result = audit.audit_for_votes()
    assert result["UNSC_Bench"]["matches_by_draft_or_meeting"] == [{"split": "adopted", "row_index": 242}]
    return result


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
