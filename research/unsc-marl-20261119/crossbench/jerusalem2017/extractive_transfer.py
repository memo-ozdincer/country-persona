"""Test the unchanged extractive selector on real Gaza writer errors."""
import argparse
from itertools import batched
import json
from pathlib import Path
from unittest.mock import patch

import extractive_chair as parent

partner = parent.partner
GAZA = partner.GAZA
BANKS = ("writer-evidence", "scoped-evidence")


def cases():
    task = partner.read(GAZA / "task.json")
    focuses = {item["id"]: item for item in task["focuses"]}
    for bank in BANKS:
        answers = partner.read(GAZA / bank / "final-records.json")[task["id"]]
        for name, text in answers.items():
            if name.endswith("/matched"):
                focus = focuses[name.split("/")[0]]
                yield f"{bank}/{name}", focus, text


def requests():
    for name, focus, answer in cases():
        data = {"focal_slip": focus["requester_card"], "archive_excerpt": focus["backup"],
                "candidate_sentences": dict(enumerate(parent.units(answer), 1))}
        yield partner.replay.request(name, 12, parent.GUIDE, data, [focus["id"]])


def episode(generate):
    rows = {}
    for group in batched(requests(), 4):
        rows.update(generate(list(group)))
    return [{"family": partner.load()["id"], "final": rows}]


def locks():
    files = (GAZA / "task.json", GAZA / "compiled-results.json", Path(__file__),
             *(GAZA / bank / name for bank in BANKS for name in ("final-records.json", "annotations.json")))
    return {**parent.locks(), **{str(file.relative_to(parent.HERE.parent)): partner.digest(file) for file in files}}


def run(directory):
    with patch.object(partner.runner, "episode", episode), patch.object(partner.runner, "locks", locks):
        partner.runner.run(Path(partner.read(partner.writer.MODEL)["model"]), directory)


def capture(directory):
    with patch.object(partner.replay, "episode", episode), patch.object(partner.replay, "locks", locks):
        return partner.replay.verify(directory)


def score(directory):
    rows = capture(directory)
    annotations = directory / "annotations.json"
    checked = partner.read(annotations)
    original = {bank: partner.read(GAZA / bank / "annotations.json")["rows"] for bank in BANKS}
    slates = partner.read(GAZA / "compiled-results.json")["rendered"]
    outcome = {}
    for name, focus, text in cases():
        bank, field, variant = name.split("/")
        former = original[bank][f"{field}/{variant}"]
        note_units = parent.units(text)
        selected = parent.selection(rows[name], len(note_units))
        saved = [] if selected is None else [note_units[i - 1] for i in selected]
        composed = " ".join([slates[f"{field}/slip"], *saved])
        recorded = checked["rows"][name]
        assert recorded["status"] in {"clear", "failed", "uncertain"} and recorded["reason"]
        for issue in recorded.get("issues", []):
            assert issue and issue in composed
        coverage = []
        for criterion, witness in former["met"].items():
            if criterion != "0" and any(witness["record"] in sentence for sentence in saved):
                coverage.append(criterion)
        for criterion in recorded.get("uncredited", []):
            assert criterion in coverage
            coverage.remove(criterion)
        issue = former.get("issues", {}).get("guard")
        raw = 42 + 7 * len(coverage)
        outcome[name] = {"previous_guard": former["guard"], "old_guard_span_retained": bool(issue and issue in composed),
                         "new_guard": recorded["status"], "words": len(composed.split()),
                         "selected": selected, "retained_previously_credited_criteria": coverage,
                         "supplement": composed, "raw": raw,
                         "strict_release": raw if len(composed.split()) <= 85 and recorded["status"] == "clear" else 0}
    assert set(outcome) == set(checked["rows"])
    return {"scope": checked["scope"], "trace_sha256": partner.digest(directory / "transcript.jsonl"),
            "annotations_sha256": partner.digest(annotations), "cases": outcome}


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("mode", choices=("run", "score"))
    cli.add_argument("directory", type=Path)
    args = cli.parse_args()
    if args.mode == "run":
        run(args.directory)
    else:
        print(json.dumps(score(args.directory), ensure_ascii=False, indent=2))
