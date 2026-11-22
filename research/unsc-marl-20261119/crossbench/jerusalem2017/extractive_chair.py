"""Select extractive chair sentences and test controlled source-fidelity foils."""
import argparse
from itertools import batched
import json
from pathlib import Path
import re
from unittest.mock import patch

import live_protocol as live

HERE = live.HERE
partner = live.partner
BANK = HERE / "live-evidence"
GUIDE = (
    "Choose which numbered note sentences may be added after the focal slip. Keep every sentence that adds "
    "supported substance about the focal item. Reject a sentence if any material detail is unsupported or "
    "contradicts the underlying source, if it is merely commentary about the note, or if its reference would be "
    "unclear after removal of another sentence. Keep proposals, attribution and outcomes distinct. "
    "Output a comma-separated list of sentence numbers in increasing order, or NONE. Do not write any prose."
)
REPLACEMENTS = {
    "us_no_request": ("did not prejudge", "settled"),
    "uk_no_request": ("remains in Tel Aviv with no plans to move", "will relocate from Tel Aviv to Jerusalem"),
    "sweden_request": ("did not alter already adopted Council resolutions", "revoked already adopted Council resolutions"),
    "draft_request": ("did not become a final Council act", "became a final Council act"),
}
BOUNDARY = re.compile(r"(?<!\b[A-Z]\.[A-Z]\.)(?<=[.!?])\s+")
DATE_PLACEHOLDER = "On [date], "


def units(text):
    result = [sentence.removeprefix(DATE_PLACEHOLDER) for sentence in BOUNDARY.split(text.strip())]
    assert all(unit and unit in text for unit in result)
    return result


def cases():
    record = partner.read(BANK / "scores.json")["pairs"]
    focuses = {f["id"]: f for f in partner.load()["focuses"]}
    for case in live.CASES:
        for arm in live.ARMS:
            previous = record[case][arm]
            if not previous["admitted_matching_note"]:
                continue
            original = previous["reply_note"]
            old, new = REPLACEMENTS[case]
            assert original.count(old) == 1
            for variant, note in (("live", original), ("foil", original.replace(old, new))):
                yield f"{case}/{arm}/{variant}", previous, focuses[previous["sent"]], note


def requests():
    for name, prev, source, raw in cases():
        data = {"focal_slip": prev["focal_slip"], "archive_excerpt": source["backup"],
                "candidate_sentences": dict(enumerate(units(raw), 1))}
        yield partner.replay.request(name, 12, GUIDE, data, [source["id"]])


def episode(generate):
    rows = {}
    for group in batched(requests(), 4):
        rows.update(generate(list(group)))
    return [{"family": partner.load()["id"], "final": rows}]


def locks():
    return {**live.locks(), "extractive_script": partner.digest(Path(__file__)),
            "live_scores": partner.digest(BANK / "scores.json"),
            "live_annotations": partner.digest(BANK / "annotations.json")}


def run(directory):
    with patch.object(partner.runner, "episode", episode), patch.object(partner.runner, "locks", locks):
        partner.runner.run(Path(partner.read(partner.writer.MODEL)["model"]), directory)


def capture(directory):
    with patch.object(partner.replay, "episode", episode), patch.object(partner.replay, "locks", locks):
        return partner.replay.verify(directory)


def selection(row, count):
    if not row["ended"]:
        return None
    if row["output"] == "NONE":
        return []
    if not re.fullmatch(r"[1-9](?:,\s*[1-9])*", row["output"]):
        return None
    chosen = [int(item) for item in row["output"].split(",")]
    return chosen if chosen == sorted(set(chosen)) and max(chosen) <= count else None


def score(directory):
    raw = capture(directory)
    reference = partner.read(BANK / "annotations.json")["rows"]
    original = partner.read(BANK / "scores.json")["pairs"]
    slip_only = partner.read(HERE / "slip-evidence/scores.json")["pairs"]
    evidence = {}
    compiled = {}
    for name, prev, source, text in cases():
        case, arm, variant = name.split("/")
        candidates = units(text)
        picked = selection(raw[name], len(candidates))
        marked = reference[f"{case}/{arm}"]["note_met"]
        mutation = REPLACEMENTS[case][1] if variant == "foil" else None
        retained = [] if picked is None else [candidates[i - 1] for i in picked]
        guard_failed = bool(mutation and any(mutation in unit for unit in retained))
        picked_record = " ".join([prev["focal_slip"], *retained])
        # For live notes exact witnesses were reviewed in the earlier transport
        # experiment. Foils score guard sensitivity only.
        met = [key for key, proof in marked.items() if proof["note"] in picked_record] if variant == "live" else []
        raw_points = 42 + 7 * len(met)
        admitted = len(picked_record.split()) <= 85 and not guard_failed
        strict = raw_points if admitted and variant == "live" else None
        evidence[name] = {"candidate_units": candidates, "selector_output": raw[name]["output"],
                          "selection": picked, "included_corrupted_sentence": guard_failed,
                          "supplement": picked_record, "retained_criteria": met,
                          "words": len(picked_record.split()), "strict_release": strict}
        if variant == "live":
            compiled[f"{case}/{arm}"] = {"raw": raw_points, "strict": strict, "supplement": picked_record,
                                          "literal_note_words": len((prev["focal_slip"] + " " + text).split()),
                                          "literal_has_date_placeholder": "[date]" in text}
    for case, observations in original.items():
        for arm, prev in observations.items():
            if prev["admitted_matching_note"]:
                continue
            compiled[f"{case}/{arm}"] = {"raw": 42, "strict": 42, "supplement": prev["focal_slip"],
                                          "literal_note_words": None, "literal_has_date_placeholder": False}
    movements = {}
    for key, row in compiled.items():
        case, arm = key.split("/")
        movements[key] = {"compiled": row["strict"], "live_freeform": original[case][arm]["strict_release"],
                          "no_public_freeform": slip_only[case][arm]["strict_release"]}
    failures = sum(row["included_corrupted_sentence"] for key, row in evidence.items() if key.endswith("/foil"))
    return {"scope": "For genuine live notes, reuse same-assistant exact coverage proofs from transport review. "
                     "Foils measure unauthorized sentence selection only. The minimal format normalization may strip a "
                     "leading date placeholder. No new margin indicates a population effect.",
            "trace_sha256": partner.digest(directory / "transcript.jsonl"),
            "common_public_record": partner.load()["public_record"], "selector_cases": evidence,
            "compiled": compiled, "strict_release_comparison": movements,
            "foils_incorrectly_admitted": failures}


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("mode", choices=("run", "score"))
    cli.add_argument("directory", type=Path)
    args = cli.parse_args()
    if args.mode == "run":
        run(args.directory)
    else:
        print(json.dumps(score(args.directory), ensure_ascii=False, indent=2))
