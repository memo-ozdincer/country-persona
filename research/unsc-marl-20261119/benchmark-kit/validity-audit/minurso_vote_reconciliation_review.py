"""Compare final records before and after public-roll-call reconciliation."""
import argparse
import json
from pathlib import Path

from minurso_deliberation_review import grade_final
from minurso_vote_reconciliation import ARCHIVES, replay, requests
from source_record_run import digest


def report(directory, annotations):
    assert annotations["transcript_sha256"] == digest(directory / "transcript.jsonl")
    outputs = replay(directory, verify_tokens=False)
    assert set(annotations["outcomes"]) == {r["id"] for r in outputs}
    all_rows = {}
    for name, path in ARCHIVES.items():
        score = json.loads((path / "score.json").read_text())
        assert score["annotations_from"] == digest(path / "transcript.jsonl")
        all_rows[name] = score["arms"]
    reports = {}
    for record, (request, audit) in zip(outputs, requests(), strict=True):
        label = record["id"]
        case, arm = label.split("-", 1)
        body = json.loads(request["messages"][1]["content"])
        visible = dict(zip(request["seen"], body["national_drafts"].values(), strict=True))
        after = grade_final(record, annotations["outcomes"][label], visible, [record])
        before = all_rows[case][arm]
        reports[label] = {"before_points": before["grounded_points"], "after_points": after["grounded_points"],
                          "before_guard": before["guard"], "after_guard": after["guard"],
                          "old_private_parts": sorted(k for k,v in before["proof_chain"].items() if "turn" in v),
                          "new_private_parts": sorted(k for k,v in after["proof_chain"].items() if "turn" in v),
                          "removed": audit, "record": after}
    return {"scope": annotations["scope"], "transcript_sha256": annotations["transcript_sha256"],
            "annotations": annotations["label"], "arms": reports}


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("directory", type=Path)
    cli.add_argument("annotations", type=Path)
    args = cli.parse_args()
    print(json.dumps(report(args.directory, json.loads(args.annotations.read_text())), ensure_ascii=False, indent=2))
