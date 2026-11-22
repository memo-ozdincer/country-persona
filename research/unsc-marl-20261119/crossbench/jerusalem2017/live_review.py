"""Validate provenance spans and compare paired live final records."""
import argparse
import json
from pathlib import Path
import random

import numpy as np

import live_protocol as live

read, digest = live.partner.read, live.partner.digest


def inputs(directory):
    rows = live.verify(directory)
    task = live.partner.load()
    choices = live.decide(live.actions(rows))
    return rows, task, choices


def blind(directory):
    rows, task, choices = inputs(directory)
    cases = [(case, arm) for case in live.CASES for arm in live.ARMS]
    random.Random(20171218).shuffle(cases)
    packets = {}
    mapping = {}
    for i, (case, arm) in enumerate(cases, 1):
        _, focus_idx, _ = live.CASES[case]
        focus = task["focuses"][focus_idx]
        row = rows[f"chair/{case}/{arm}"]
        payload = json.loads(row["messages"][1]["content"])
        if "archival_backup" in payload:
            payload["underlying_source"] = focus["backup"]
        key = f"J{i:02}"
        packets[key] = {"rules": {"criteria": focus["criteria"], "guard": task["guard"], "word_cap": 85},
                        "evidence": payload, "candidate": row["output"]}
        mapping[key] = f"{case}/{arm}"
    return {"packets": packets, "private_mapping": mapping}


def exact(text, quote):
    assert quote and quote in text, quote


def review(directory):
    rows, task, choices = inputs(directory)
    annotation = directory / "annotations.json"
    data = read(annotation)
    assert data["scope"]
    assert set(data["rows"]) == {f"{case}/{arm}" for case in live.CASES for arm in live.ARMS}
    schedules = live.actions(rows)
    output = {}
    for case, (desk, index, inventory) in live.CASES.items():
        focus = task["focuses"][index]
        output[case] = {}
        for arm, retained in choices[case].items():
            name = f"{case}/{arm}"
            source = task["focuses"][retained]
            sent = rows[f"note/{name}"]
            final = rows[f"chair/{name}"]
            labels = data["rows"][name]
            relevant = index == retained
            attached = len(final["evidence_ids"]) == 2
            assert attached == (relevant and live.admitted(sent))
            assert retained in inventory
            note_coverage = labels["note_met"]
            assert note_coverage.keys() <= set("1234")
            assert labels["guard"] in {"clear", "failed", "uncertain"} and labels["reason"]
            for spans in note_coverage.values():
                exact(sent["output"], spans["note"])
                exact(source["backup"], spans["source"])
            for quote in labels.get("note_issues", {}).values():
                exact(sent["output"], quote)
            assert labels["met"].keys() <= set("01234")
            for criterion, spans in labels["met"].items():
                exact(final["output"], spans["record"])
                if criterion == "0":
                    exact(focus["slip"], spans["source"])
                else:
                    assert attached and criterion in note_coverage
                    exact(sent["output"], spans["note"])
            for quote in labels.get("issues", {}).values():
                exact(final["output"], quote)
            raw = 35 + 7 * len(labels["met"])
            released = final["ended"] and len(final["output"].split()) <= 85 and labels["guard"] == "clear"
            request = schedules[desk]["mission"][index]
            output[case][arm] = {
                "request_delivered": task["question"] if request else None,
                "sent": source["id"], "admitted_matching_note": attached,
                "focal_slip": focus["slip"], "reply_note": sent["output"], "supplement": final["output"],
                "peer_turns_attempted": request + 1,
                "peer_turns_passing_format_gate": request + int(live.admitted(sent)),
                "note_issues": list(labels.get("note_issues", {})),
                "distinct_source_criteria_in_note": list(note_coverage),
                "distinct_relevant_criteria_delivered": list(note_coverage) if attached else [],
                "distinct_relevant_criteria_in_record": [key for key in labels["met"] if key != "0"],
                "raw": raw, "strict_release": raw if released else 0, "guard": labels["guard"],
                "supplement_words": len(final["output"].split()),
                "generated_tokens_note_and_chair": len(sent["output_ids"]) + len(final["output_ids"]),
            }
    fields = ("raw", "strict_release")
    margins = {case: {field: result["calibrated"][field] - result["uncalibrated"][field] for field in fields}
               for case, result in output.items()}
    calibration = live.transfer.Calibration()
    calibration.points[:, 1] = 70
    blind_decoder = calibration.receiver(np.full(4, .5), calibration.design_prior)
    rosters = {tuple(pair): i for i, pair in enumerate(live.transfer.routing.PAIR)}
    controls = {}
    for case, (desk, focus, inventory) in live.CASES.items():
        sender = np.asarray(schedules[desk]["mission"])
        query = sender[focus]
        right = rosters[inventory]
        oracle = calibration.receiver(sender, calibration.design_prior)
        wanted = {"blind_exact": blind_decoder[right, query], "known_sender": oracle[right, query],
                  "both_inventories": focus}
        controls[case] = {}
        for name, decision in wanted.items():
            # The two original arms cover both legal source choices. Reuse the
            # observed record for that source, with no additional writer call.
            observed_arm, = [arm for arm, source in choices[case].items() if source == decision]
            record = output[case][observed_arm]
            controls[case][name] = {"source_arm": observed_arm,
                                    **{field: record[field] for field in fields}}
    return {"scope": data["scope"], "common_public_record": task["public_record"],
            "trace_sha256": digest(directory / "transcript.jsonl"),
            "annotation_sha256": digest(annotation), "pairs": output, "margins": margins, "reused_controls": controls}


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("mode", choices=("score", "blind"))
    cli.add_argument("directory", type=Path)
    args = cli.parse_args()
    print(json.dumps(review(args.directory) if args.mode == "score" else blind(args.directory),
                     indent=2, ensure_ascii=False))
