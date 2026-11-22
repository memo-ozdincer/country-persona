"""Replay two explicit received-constraint checks on the Syria trace."""
import argparse
import json
from pathlib import Path
import sys

from run import ROOT, FAMILY, inputs
from packets import packet

sys.path.insert(0, str(ROOT.parent / "judge"))
from score import score


def evaluate(path):
    records = {r["id"]: r for line in path.read_text().splitlines() for r in [json.loads(line)]}
    given, _ = inputs()
    case = next(f for f in given["families"] if f["id"] == FAMILY)
    out = {}
    for variant, peer_quote, revision, card_quote, result, reason in (
        ("overlap", 'mandatory "additional" checkpoint',
         'The UK\'s "additional" checkpoint requirement excludes A and D, leaving only B as potentially compatible',
         '"checkpoint": "additional"', "used",
         "The peer supplied a constraint that the revision uses to justify the unique overlap. "
         "The independent revision also recommends B, without the UK constraint."),
        ("impasse", "my operative condition is a six-month authorization",
         "The UK delegate's six-month condition creates a deadlock; their preference for D does not override my nine-month requirement.",
         '"duration": "six"', "uncertain",
         "The revision recognizes the clash but then proposes advancing A, which the stated UK mandate excludes. "
         "The evidence establishes transfer of the constraint but does not establish a coherent changed joint disposition."),
    ):
        for_state = next(v for v in case["variants"] if v["id"] == variant)
        blocks = packet(case, for_state, given["boundary"], "judge")["evidence"]
        other, final, before, solo = (records[k] for k in (
            f"open-2-{variant}", f"peer-1-{variant}", "open-1-shared", "solo-1-shared"))
        assert final["dependencies"] == [before["id"], other["id"]]
        event = {"id": "U1", "peer": other["output"], "revision": final["output"],
                 "opening": before["output"], "solo_revision": solo["output"]}
        target = {"id": f"received-constraint-{variant}", "mode": "MECHANISM",
                  "task": "Find whether Brazil used the received UK condition in a consequential, supported revision.",
                  "evidence": blocks, "opportunities": [event]}
        verdict = {"id": target["id"], "opportunities": [{
            "id": event["id"], "status": result, "peer_specific": result == "used",
            "peer": peer_quote, "revision": revision, "source": [{"block": "workshop-card-2", "quote": card_quote}],
            "reason": reason,
        }]}
        out[variant] = {"request": target, "same_assistant_verdict": verdict, "score": score(target, verdict)}
    return out


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("transcript", type=Path)
    print(json.dumps(evaluate(cli.parse_args().transcript), indent=2, ensure_ascii=False))
