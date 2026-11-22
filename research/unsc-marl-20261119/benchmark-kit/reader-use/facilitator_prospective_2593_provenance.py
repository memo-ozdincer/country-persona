"""Match the official Resolution 2593 roll call to both benchmark releases."""
import json
from unittest.mock import patch

import facilitator_emergency_session_provenance as audit
import facilitator_prospective_2593 as study


def report():
    packet = study.packet()
    event = {"UNBench_event": str(packet["benchmark_identifiers"]["UNBench"]),
             **{k: packet[k] for k in ("date", "meeting", "draft")}}
    yes = ("Estonia", "France", "India", "Ireland", "Kenya", "Mexico", "Niger", "Norway",
           "Saint Vincent and the Grenadines", "Tunisia", "United Kingdom", "United States", "Viet Nam")
    official = {audit.country_name(name): "Y" for name in yes}
    official.update({audit.country_name(name): "A" for name in ("China", "Russian Federation")})
    with patch.object(audit.study, "packet", return_value={"event": event}), patch.object(audit, "OFFICIAL", official):
        result = audit.audit_for_votes()
    assert result["UNSC_Bench"]["matches_by_draft_or_meeting"] == [packet["benchmark_identifiers"]["UNSC-Bench"]]
    return result


if __name__ == "__main__":
    print(json.dumps(report(), indent=2))
