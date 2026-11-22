"""Compare live clarification, independent desks, and a three-pass solo analyst."""
import argparse
from itertools import product
import json
from pathlib import Path
from unittest.mock import patch

import facilitator_new_meetings as related

HERE = related.HERE
FAMILY = "facilitator-live-peers"
runner = related.runner
chair = related.chair
ARMS = ("peer", "independent", "solo")
OPEN_CAP, REPLY_CAP, FINAL_CAP = 75, 75, 112

OPENING = (
    "Review the proposed sentence against the card for the focal delegation. Return two short sentences: "
    "one describing the strongest supported fact or an evidence gap, and one asking what the other delegation "
    "actually said about the proposal. Name the object, scope or capacity that needs checking. Do not answer "
    "for the other delegation. Use the card as evidence and avoid unsupported claims."
)
REPLY = (
    "Check the focal delegation's part of the proposed joint statement against that delegation's card. "
    "If you receive a working note and question, use the question to focus your check. Record what the "
    "delegation actually said, and identify any evidence gap about the precise proposition. A true statement "
    "about a different referent does not prove or contradict the proposition. Preserve distinctions between "
    "the scope of a resolution and the scope of a treaty, and between speaking for oneself and for a group. "
    "Use at most two short sentences. Return the relevant position and qualification."
)
FINAL = (
    "Write the source-grounded facilitator's final record. Return one line: retain, revise, or withhold, "
    "followed by a vertical bar and a brief of at most 48 words. Retain if both sources establish both sides "
    "of the proposed joint statement. Revise if a source explicitly contradicts a side. Otherwise withhold. "
    "In the brief, give each delegation's actual relevant position or mark the precise evidence gap. "
    "Include exact bracketed passage IDs [S1] and [S2] with factual attributions. A proposal, statement, "
    "vote and collective Council decision are distinct. Verify working notes against the documentary passages."
)


def panels():
    for family, docket in chair.load(related.PACK).items():
        proposal, predicate, truth = docket["proposals"][2]
        cards = {f"S{i}": {"delegation": actor, "passage": source}
                 for i, (actor, source) in enumerate(docket["sources"], 1)}
        for first, second in (("S1", "S2"), ("S2", "S1")):
            yield f"{family}-{first}", proposal, predicate, tuple(truth), cards, first, second


def opening_requests():
    for panel, claim, _, _, cards, first, second in panels():
        for arm, visible in (("desk", {first: cards[first]}), ("solo", cards)):
            payload = {"proposed_sentence": claim, "focal_card": first, "documentary_passages": visible,
                       "other_delegation": cards[second]["delegation"]}
            yield related.transfer.prompt(f"{panel}/{arm}/opening", OPEN_CAP, OPENING, payload)


def reply_requests(rows):
    for panel, claim, predicate, _, cards, first, second in panels():
        for arm in ARMS:
            payload = {"proposed_sentence": claim, "focal_card": second,
                       "target_assertion": f"{cards[second]['delegation']} {predicate}.",
                       "documentary_passages": cards if arm == "solo" else {second: cards[second]}}
            if arm != "independent":
                key = f"{panel}/{'solo' if arm == 'solo' else 'desk'}/opening"
                payload["working_note_and_question"] = rows[key]["output"]
            yield related.transfer.prompt(f"{panel}/{arm}/reply", REPLY_CAP, REPLY, payload)


def final_requests(rows):
    for panel, claim, _, _, cards, first, second in panels():
        for arm in ARMS:
            opener = f"{panel}/{'solo' if arm == 'solo' else 'desk'}/opening"
            reply = f"{panel}/{arm}/reply"
            payload = {"proposed_sentence": claim, "documentary_passages": cards,
                       "working_notes": {first: rows[opener]["output"], second: rows[reply]["output"]}}
            yield related.transfer.prompt(f"{panel}/{arm}/final", FINAL_CAP, FINAL, payload)


def generate_episode(generate):
    rows = generate(list(opening_requests()))
    rows.update(generate(list(reply_requests(rows))))
    rows.update(generate(list(final_requests(rows))))
    return [{"family": FAMILY, "final": rows}]


def pins():
    archive = related.pins()
    path = Path(__file__).resolve()
    archive[str(path.relative_to(HERE.parents[1]))] = runner.digest(path)
    return archive


def verify(directory):
    locked = pins()
    module = related.transfer
    with patch.multiple(module, local=opening_requests, audits=reply_requests, syntheses=final_requests,
                        pins=lambda: locked, FAMILY=FAMILY):
        return module.read(directory)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("run", "verify"))
    parser.add_argument("directory", type=Path)
    parser.add_argument("--model", type=Path)
    args = parser.parse_args()
    if args.mode == "run":
        with patch.multiple(runner, episode=generate_episode, locks=pins):
            runner.run(args.model, args.directory)
    else:
        print(json.dumps({"generations": len(verify(args.directory))}))
