"""Compare typed live peer findings against independent checks and a solo analyst."""
import argparse
import json
from pathlib import Path
from unittest.mock import patch

import facilitator_event_transfer as transfer
import facilitator_live_peers as live

HERE = transfer.HERE
FAMILY = "facilitator-peer-findings"
runner = transfer.runner
ARMS = live.ARMS
CAP = 75
FINAL_CAP = live.FINAL_CAP
LABELS = ("supports", "contradicts", "unknown")
CHECK = (
    "Check the one-speaker assertion against the focal delegation's card. "
    "Answer supports only if it establishes the entire assertion, contradicts only if the same speaker "
    "clearly said or did something incompatible on the same object or scope, otherwise unknown. "
    "Distinguish evidence about a different referent, a narrower claim, or a gap from evidence of conflict. "
    "If a peer finding is supplied, check its qualification before considering your own card. "
    "Return the lowercase label, a comma, and an exact contiguous source excerpt of at most 22 words. "
    "The excerpt must preserve the relevant actor and qualification. For unknown, use only the lowercase word unknown."
)
FINAL = live.FINAL + (
    " Read the source-local findings separately. A verified contradiction requires a revise heading even "
    "when the other side is unknown. The findings are working notes. Use the passages to verify them."
)


def panels():
    all_live = list(live.panels())
    for key, claim, predicate, truth, cards, first, second in all_live:
        if key in ("guinea-S2", "libya-S1"):
            yield key, claim, predicate, truth, cards, first, second
    for panel, claim, predicate, truth, cards in transfer.panels():
        if panel.startswith("central-african-republic-"):
            mapped = {f"S{i}": {"delegation": actor, "passage": source} for i, (actor, source) in enumerate(cards, 1)}
            yield panel, claim, predicate, truth, mapped, "S1", "S2"


def opening_requests():
    for panel, _, predicate, _, cards, first, _ in panels():
        for arm, visible in (("desk", {first: cards[first]}), ("solo", cards)):
            payload = {"focal_card": first, "documentary_passages": visible,
                       "assertion": f"{cards[first]['delegation']} {predicate}."}
            yield transfer.prompt(f"{panel}/{arm}/opening", CAP, CHECK, payload)


def reply_requests(rows):
    for panel, _, predicate, _, cards, _, second in panels():
        for arm in ARMS:
            payload = {"focal_card": second, "documentary_passages": cards if arm == "solo" else {second: cards[second]},
                       "assertion": f"{cards[second]['delegation']} {predicate}."}
            if arm != "independent":
                mode = "solo" if arm == "solo" else "desk"
                payload["prior_finding"] = rows[f"{panel}/{mode}/opening"]["output"]
            yield transfer.prompt(f"{panel}/{arm}/reply", CAP, CHECK, payload)


def findings(row, source):
    raw = row["output"].strip()
    label, separator, quote = (part.strip() for part in raw.partition(","))
    if row["ended"] and label in LABELS[:2] and separator and 0 < len(quote.split()) <= 22 and quote in source:
        return {"relation": label, "excerpt": quote}
    return {"relation": "unknown", "excerpt": None}


def notes(panel, arm, rows, cards, first, second):
    opening = f"{panel}/{'solo' if arm == 'solo' else 'desk'}/opening"
    return {first: findings(rows[opening], cards[first]["passage"]),
            second: findings(rows[f"{panel}/{arm}/reply"], cards[second]["passage"])}


def final_requests(rows):
    for panel, claim, _, _, cards, first, second in panels():
        for arm in ARMS:
            payload = {"proposed_sentence": claim, "documentary_passages": cards,
                       "working_notes": notes(panel, arm, rows, cards, first, second)}
            yield transfer.prompt(f"{panel}/{arm}/final", FINAL_CAP, FINAL, payload)


def episode(generate):
    rows = generate(list(opening_requests()))
    rows.update(generate(list(reply_requests(rows))))
    rows.update(generate(list(final_requests(rows))))
    return [{"family": FAMILY, "final": rows}]


def pins():
    result = live.pins()
    for path in (Path(__file__), transfer.PACK):
        result[str(path.resolve().relative_to(HERE.parents[1]))] = runner.digest(path)
    return result


def verify(directory):
    locked = pins()
    with patch.multiple(transfer, local=opening_requests, audits=reply_requests, syntheses=final_requests,
                        pins=lambda: locked, FAMILY=FAMILY):
        return transfer.read(directory)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("run", "verify"))
    parser.add_argument("directory", type=Path)
    parser.add_argument("--model", type=Path)
    args = parser.parse_args()
    if args.mode == "run":
        with patch.multiple(runner, episode=episode, locks=pins):
            runner.run(args.model, args.directory)
    else:
        print(json.dumps({"verified": len(verify(args.directory))}))
