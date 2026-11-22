"""Run fresh probes, local replies and chair records in paired Jerusalem episodes."""
import argparse
from itertools import batched
import json
from pathlib import Path
from unittest.mock import patch

import numpy as np

import estimate_receiver
import factored_partner
import language_partner as partner
import transfer

HERE = partner.HERE
CASES = {
    "us_no_request": ("draft_desk", 1, (1, 2)),
    "uk_no_request": ("draft_desk", 2, (1, 2)),
    "sweden_request": ("statement_desk", 3, (0, 3)),
    "draft_request": ("draft_desk", 0, (0, 1)),
}
ARMS = ("calibrated", "uncalibrated")
GUIDE = (
    "Send a faithful one-paragraph summary of the one source you have been asked to relay. Use at most "
    "65 words. Preserve speaker capacity and attribution, dates, references, uncertainty and any distinction "
    "between a draft proposal and a Council act. Do not borrow facts from any other document. Output only the note."
)


def read_fit():
    calibration = transfer.Calibration()
    model = partner.read(HERE / "estimated-receiver.json")
    background = calibration.design_prior.T
    conditional = background / background.sum(axis=1, keepdims=True)
    table = estimate_receiver.table(conditional, np.asarray(model["emission"]), np.full(4, 28))
    return calibration.fitted_receiver, table


def plan():
    task = partner.load()
    expected = {case: {arm: int(action) for arm, action in choices.items()}
                for case, choices in decide(transfer.EXPECTED).items()}
    return {"scope": "Four preselected intact-delivery contrasts. The no-request pair has identical responder "
                     "inventories and opposite relevant backups. The draft case tests the authority distinction. "
                     "These cases are mechanisms, not a population estimate.",
            "task": task["id"], "cases": CASES, "expected_source_indices": expected,
            "focus_order": [focus["id"] for focus in task["focuses"]],
            "request_or_pass": task["question"], "note_word_cap": 65, "note_token_cap": 112,
            "chair_token_cap": 160}


def actions(rows):
    categories = dict.fromkeys(("probe", "mission"))
    for phase in categories:
        categories[phase] = []
        for focus in partner.load()["focuses"]:
            row = rows[f"{phase}/{focus['id']}"]
            accepted = row["ended"] and row["output"] in ("DRAFT", "STATEMENT")
            if not accepted:
                raise ValueError(f"Invalid source classification: {row['id']}")
            categories[phase].append(row["output"])
    return {desk: {phase: [int(value == target) for value in labels]
                   for phase, labels in categories.items()} for desk, target in factored_partner.POLICY.items()}


def decide(schedules):
    blind, table = read_fit()
    masks = {tuple(pair): i for i, pair in enumerate(transfer.routing.PAIR)}
    out = {}
    for case, (desk, focus, inventory) in CASES.items():
        seen = int(np.asarray(schedules[desk]["probe"]) @ np.asarray([8, 4, 2, 1]))
        query = schedules[desk]["mission"][focus]
        row = masks[inventory]
        out[case] = {"calibrated": int(table[seen, row, query]), "uncalibrated": int(blind[row, query])}
    return out


def note_requests(selected):
    focuses = partner.load()["focuses"]
    for case, choices in selected.items():
        for method, source in choices.items():
            focus = focuses[source]
            yield partner.replay.request(
                f"note/{case}/{method}", 112, GUIDE,
                {"source": focus["backup"], "source_id": focus["id"]}, [focus["id"]],
            )


def admitted(note):
    output = note["output"]
    return note["ended"] and 0 < len(output.split()) <= 65 and output.endswith(".")


def chair_requests(notes, selected):
    task = partner.load()
    for case, (_, focus_idx, _) in CASES.items():
        focus = task["focuses"][focus_idx]
        for method in ARMS:
            reply = notes[f"note/{case}/{method}"]
            source_is_relevant = selected[case][method] == focus_idx
            matched = source_is_relevant and admitted(reply)
            payload = {"public_record": task["public_record"], "focal_slip": focus["slip"],
                       "coverage": focus["criteria"] if matched else focus["criteria"][:1]}
            evidence_ids = [f"{focus['id']}/slip"]
            if matched:
                payload["archival_backup"] = reply["output"]
                evidence_ids.append(f"{focus['id']}/backup")
            yield partner.replay.request(f"chair/{case}/{method}", 160, partner.writer.GUIDE, payload, evidence_ids)


def batches(generate, requests):
    output = {}
    for group in batched(requests, 4):
        output.update(generate(list(group)))
    return output


def episode(generate):
    source_classes = batches(generate, factored_partner.requests())
    schedules = actions(source_classes)
    selected = decide(schedules)
    notes = batches(generate, note_requests(selected))
    chairs = batches(generate, chair_requests(notes, selected))
    return [{"family": partner.load()["id"], "final": {**source_classes, **notes, **chairs}}]


def locks():
    paths = (Path(__file__), HERE / "live-plan.json", HERE / "estimated-receiver.json",
             HERE / "record-evidence/scores.json", Path(factored_partner.__file__), Path(partner.writer.__file__),
             Path(estimate_receiver.__file__), transfer.GAZA / "prior-blind-results.json",
             transfer.GAZA / "routing-fit.json")
    return {**partner.locks(), **{file.name: partner.digest(file) for file in paths}}


def run(directory):
    assert json.loads(json.dumps(plan())) == partner.read(HERE / "live-plan.json")
    with patch.object(partner.runner, "episode", episode), patch.object(partner.runner, "locks", locks):
        partner.runner.run(Path(partner.read(partner.writer.MODEL)["model"]), directory)


def verify(directory):
    with patch.object(partner.replay, "episode", episode), patch.object(partner.replay, "locks", locks):
        return partner.replay.verify(directory)


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("mode", choices=("plan", "run", "verify"))
    cli.add_argument("directory", type=Path, nargs="?")
    args = cli.parse_args()
    if args.mode == "run":
        run(args.directory)
    elif args.mode == "plan":
        print(json.dumps(plan(), ensure_ascii=False, indent=2))
    else:
        print(json.dumps({key: row["output"] for key, row in verify(args.directory).items()}, ensure_ascii=False, indent=2))
