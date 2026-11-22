"""Evaluate individually reviewed generated fields on unchanged route receipts."""
import json
from unittest.mock import patch

import field_outcomes as scoring
import field_revision as revision
import field_authority as authority
import field_update as update

HERE = scoring.HERE


def variants():
    yield "first", scoring.approved_fields()
    for name, subdir, plan, locks, tasks in (
        ("revised", "field-revision-evidence", revision.plans, revision.locks, revision.REVISION),
        ("authority", "field-authority-evidence", authority.plan, authority.locks, authority.REQUESTS),
        ("update", "field-update-evidence", update.plan, update.locks, {"ADDITIONAL": update.TASK}),
    ):
        directory = HERE / subdir
        with patch.multiple(revision.base, plan=plan, locks=locks, TASKS=tasks):
            items = revision.base.replay(directory)
        fields = scoring.review_fields(items, directory / "transcript.jsonl",
                                      HERE / subdir.replace("-evidence", "-annotations.json"))
        yield name, fields


def run():
    assessed = dict(variants())
    accepted = {}
    selected = {}
    for key in scoring.REQUIRED:
        options = [(name, fields[key]) for name, fields in assessed.items() if key in fields
                   and fields[key]["complete"] and fields[key]["citation_ids_clear"] and fields[key]["semantic_clear"]]
        assert options, key
        phase, selected[key] = max(options, key=lambda item: (len(item[1]["met"]), -item[1]["output_tokens"]))
        accepted[key] = phase
    with patch.object(scoring, "approved_fields", return_value=selected):
        assembled = scoring.run()
    original = json.loads((HERE / "receipt-evidence/results.json").read_text())
    for name, routes in assembled["route_outcomes"].items():
        for route, item in routes.items():
            historical = original["routes"][name]["mean"][route]
            item["licensed_points"] = historical["licensed_record_points"]
            item["whole_packet_input_tokens"] = historical["writer_input_tokens"]
            item["whole_packet_output_tokens"] = historical["writer_output_tokens"]
            item["whole_packet_release"] = historical["release_probability"]
            item["whole_packet_points"] = historical["record_points"]
    return {"scope": "Measurements with review-based selection across exposed variants. Selection uses "
                     "same-assistant predicates, so the result is a writer diagnostic and not a blind release test. "
                     "All body fragments are actual frozen-model text, composed with the earlier authored vote line. "
                     "Routing decisions are kept fixed.",
            "chosen_variant": accepted, "observed_variants": assessed, "composed": assembled}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, ensure_ascii=False))
