"""Test fresh natural-language replies to an explicit two-record clarification."""
import argparse
from itertools import batched
import json
from pathlib import Path
from unittest.mock import patch

import explicit_resolution as resolution

HERE = resolution.HERE
review = resolution.context.witness
partner = review.partner
NATIONAL = "indonesia_national"
PRESIDENT = "council_president"
IDS = (NATIONAL, PRESIDENT)
CHOICES = {
    "national": ("one", (NATIONAL,)),
    "president": ("one", (PRESIDENT,)),
    "both": ("all", IDS),
    "either": ("any", IDS),
    "clarify": None,
}
DESCRIPTIONS = {
    "national": "Indonesia's national policy explanation only.",
    "president": "The Council President's certified vote transmission only.",
    "both": "Both the national explanation and certified vote transmission.",
    "either": "Either record is sufficient.",
    "clarify": "No clear in-scope choice. Further clarification or a different menu is needed.",
}
ORDERS = (tuple(CHOICES), ("either", "clarify", "president", "national", "both"))
SNIPPETS = {
    "both_short": ("Both, please.", "both"),
    "both_paraphrased": ("Include the policy statement and the tally letter as separate items.", "both"),
    "either_short": ("Either will do. One is enough.", "either"),
    "choose_from_two": ("You can pick one, whichever is available.", "either"),
    "national_only": ("Just what he argued on behalf of Indonesia.", "national"),
    "president_only": ("Only the formal message that gave members the result.", "president"),
    "self_correction": ("Both, actually no, leave out the policy statement and just send the result letter.", "president"),
    "acknowledgement_only": ("Yes, thanks.", "clarify"),
    "missing_referent": ("Just the one from Djani.", "clarify"),
    "unresolved_revision": ("Both, unless the tally might be enough. I haven't decided.", "clarify"),
    "new_object": ("Actually I'd like the U.S. explanation instead.", "clarify"),
    "negated_two": ("I don't want either of those records.", "clarify"),
}
GUIDE = (
    "Interpret the user's reply to the clarification menu. Choose the one option the reply explicitly commits to, "
    "including both or either when requested. Follow a clear latest correction. If their reply merely acknowledges "
    "the question, leaves the choice unresolved, asks for another record, or declines all the offered records, "
    "choose the no-clear-choice option. A reference to the same author alone does not distinguish the records. "
    "Output only the letter identifying the option."
)


def requests():
    for id, (reply, _) in SNIPPETS.items():
        for i, order in enumerate(ORDERS):
            choices = dict(zip("ABCDE", (DESCRIPTIONS[key] for key in order), strict=True))
            yield partner.replay.request(f"{id}/{i}", 4, GUIDE, {"clarification_options": choices, "reply": reply}, [])


def episode(generate):
    results = {}
    for group in batched(requests(), 8):
        results.update(generate(list(group)))
    return [{"family": "written-vote-clarification", "final": results}]


def locks():
    files = (Path(__file__), Path(resolution.__file__), HERE / "explicit-resolution-results.json", partner.writer.MODEL)
    return {path.name: partner.digest(path) for path in files}


def run(directory):
    with patch.object(partner.runner, "episode", episode), patch.object(partner.runner, "locks", locks):
        partner.runner.run(Path(partner.read(partner.writer.MODEL)["model"]), directory)


def report(directory):
    with patch.object(partner.replay, "episode", episode), patch.object(partner.replay, "locks", locks):
        rows = partner.replay.verify(directory)
    result = {}
    for name, (reply, expected) in SNIPPETS.items():
        observed = []
        for i, order in enumerate(ORDERS):
            row = rows[f"{name}/{i}"]
            observed.append(order[ord(row["output"]) - ord("A")]
                            if row["ended"] and row["output"] in tuple("ABCDE") else None)
        chosen = observed[0] if observed[0] == observed[1] else None
        spec = CHOICES.get(chosen)
        confirmed = resolution.confirm({"mode": spec[0], "records": list(spec[1])}) if spec else None
        result[name] = {"reply": reply, "reference": expected, "labels": observed, "consensus": chosen, "intent": confirmed,
                        "correct_selection": expected == chosen, "wrong_dispatch": confirmed is not None and chosen != expected}
    return {"scope": "Fresh frozen-model interpretations of authored clarification replies, with two label orders. "
                     "No human responses or external dispatches were observed.",
            "trace_sha256": partner.digest(directory / "transcript.jsonl"), "records": result}


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("mode", choices=("run", "score"))
    cli.add_argument("directory", type=Path)
    args = cli.parse_args()
    if args.mode == "run":
        run(args.directory)
    else:
        print(json.dumps(report(args.directory), ensure_ascii=False, indent=2))
