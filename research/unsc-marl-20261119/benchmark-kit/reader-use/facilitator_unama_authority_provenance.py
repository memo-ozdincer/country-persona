"""Check Resolution 2626 against both benchmark releases and the official vote."""
import json
from unittest.mock import patch

import facilitator_requested_evidence_provenance as audit
import facilitator_unama_authority as study

IN_FAVOUR = (
    "Albania", "Brazil", "China", "France", "Gabon", "Ghana", "India", "Ireland", "Kenya",
    "Mexico", "Norway", "United Arab Emirates", "United Kingdom", "United States",
)


def report():
    with patch.object(audit.experiment, "packet", study.packet), patch.object(audit, "OFFICIAL_IN_FAVOUR", IN_FAVOUR):
        result = audit.run()
    assert result["UNSC_Bench"]["matches_by_draft_or_meeting"] == [{"split": "adopted", "row_index": 238}]
    return result


if __name__ == "__main__":
    print(json.dumps(report(), indent=2))
