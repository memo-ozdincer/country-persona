"""Replace only the three diagnosed fields and replay the same frozen policies."""
import json
from unittest.mock import patch

import field_outcomes as baseline
import field_revision as revision

HERE = baseline.HERE
REVISED = HERE / "field-revision-evidence"


def run():
    with patch.multiple(revision.base, plan=revision.plans, locks=revision.locks, TASKS=revision.REVISION):
        replayed = revision.base.replay(REVISED)
    changed = baseline.review_fields(replayed, REVISED / "transcript.jsonl", HERE / "field-revision-annotations.json")
    initial = baseline.approved_fields()
    assert set(changed) == {"ADDITIONAL", "BRAZIL", "overlap"}
    with patch.object(baseline, "approved_fields", return_value={**initial, **changed}):
        results = baseline.run()
    whole = json.loads((HERE / "receipt-evidence/results.json").read_text())
    earlier = json.loads((HERE / "field-evidence/results.json").read_text())
    expected = {}
    _, bank = baseline.writer.compile_bank()
    deltas = {}
    for key, packet in results["packets"].items():
        reference = bank[frozenset(key.split(","))]
        assert packet["points"] <= reference["record_points"]
        deltas[key] = {"before": earlier["packets"][key]["points"], "after": packet["points"],
                       "required": reference["record_points"], "releasable": packet["release"]}
    for case, rows in results["route_outcomes"].items():
        expected[case] = {}
        for name, row in rows.items():
            original = whole["routes"][case]["mean"][name]
            expected[case][name] = {**row, "original_net_gain": original["net_gain_over_actual_anchor"],
                                    "archive_scored_record_points": original["licensed_record_points"],
                                    "old_writer_calls": 1,
                                    "old_writer_input_tokens": original["writer_input_tokens"],
                                    "old_writer_output_tokens": original["writer_output_tokens"],
                                    "release_change_since_initial_split": (row["release_probability"] -
                                        earlier["route_outcomes"][case][name]["release_probability"])}
    return {"scope": "Adaptive same-docket revisions prompted after the initial field failures were observed. "
                     "The roll call and two passing fields are unchanged. All remaining text is jointly assembled "
                     "from completed model generations. The specialist and controls retain previously frozen routing.",
            "changed_fields": changed, "record_replay": deltas,
            "route_outcomes": expected, "assembled": results["packets"]}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, ensure_ascii=False))
