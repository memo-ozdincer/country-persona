"""Generate final memos from the actual before/after ranked evidence trail."""
import argparse
from contextlib import contextmanager
from hashlib import sha256
import json
from pathlib import Path
from unittest.mock import patch

import relay_compiled_record as compiler
import relay_compromise as ranked
import relay_final_memo as generation

HERE = Path(__file__).resolve().parent
EVIDENCE = ranked.relay.KIT / "evidence"
CLARIFICATION = EVIDENCE / "relay-ranked-clarification"
ROOTS = {"venezuela": "venezuela", "space": "outer_space"}
SYSTEM = (
    "Write an English decision memo for an internal fictional UN-linked workshop. "
    "Keep attributed workshop statements and the historical UN record distinct. "
    "Use only the dossier. Report observations as supplied and give no fictional decision official authority."
)
GUIDE = (
    "Write at most 120 words. First line exactly 'Workshop status: ' followed by checked_status. "
    "Name the two card owners and their relevant grades, or identify the missing owner. "
    "Compare the selected package with another mutually acceptable package, or give the evidence for impasse or uncertainty. "
    "If a correction is supplied, explain what changed using its exact package and grade. "
    "A reported grade on an unverified card must be attributed as reported. "
    "Include both numbered historical claims with the correct instrument and the reason for the outcome. "
    "State explicitly that the workshop has no official authority."
)
CAP = 180


def sample():
    base = json.loads((CLARIFICATION / "report.json").read_text())
    guard = json.loads((CLARIFICATION / "guard.json").read_text())
    repaired = [r for r in guard["rows"] if r["strategy"] == "lowest_margin" and r["supporting_spans"]]
    assert len(repaired) == 3 and all(r["family"] == "venezuela" for r in repaired)
    for new in repaired:
        prior = next(r["arms"]["no_query/none"] for r in base["outcomes"]["venezuela"] if r["world"] == new["world"])
        assert prior["choice"] == new["choice"] and prior["received"] != new["after"]
        yield "venezuela", tuple(new["world"]), "reported", tuple(prior["received"]), prior["choice"], []
        yield "venezuela", tuple(new["world"]), "verified", tuple(new["after"]), new["choice"], new["supporting_spans"]
    middle = repaired[0]
    yield "venezuela", tuple(middle["world"]), "withheld", (0, middle["after"][1]), "unresolved", []
    yield "space", (2, 16), "verified-tie", (2, 16), "F", []


def suite():
    specs = compiler.load(compiler.MANIFEST)
    fixtures = ranked.fixtures()
    for family, world, arm, delivered, answer, spans in sample():
        task = fixtures[family]
        spec = specs[ROOTS[family]]
        historical = compiler.read_authority(spec)
        roles = spec["roles"]
        cards = []
        for seat, card_id in enumerate(delivered):
            if card_id:
                grades = dict(zip(task.actions[:-1], task.card(seat, card_id), strict=True))
                cards.append({"owner": roles[seat], "verification": "reported" if arm == "reported" and seat == 0 else "verified",
                              "grades": {k: g for k, g in grades.items() if g}})
        payload = {
            "scenario": f"Fictional {family} drafting workshop. Scores express only the exercise mandates.",
            "checked_status": answer.upper(),
            "status_basis": "The status is provisional on the reported card." if arm == "reported" else "Use only the evidence received.",
            "rule": "Omitted packages are rejected. Maximize the lower of the two grades among mutually accepted packages, then their sum. An exact tie allows either package. With a missing card, use unresolved when the evidence cannot decide.",
            "possible_card_holders": roles,
            "received_cards": cards,
            "correction": {"owner": roles[0], "package": "B", "grade": 1, "evidence": spans} if spans else None,
            "historical_evidence": historical,
            "instruction": GUIDE,
        }
        yield {"id": f"{family}/{world[0]}-{world[1]}/{arm}", "family": family, "arm": arm,
               "expected": payload, "messages": [{"role": "system", "content": SYSTEM},
                                                 {"role": "user", "content": json.dumps(payload, ensure_ascii=False)}]}


def sources():
    specs = compiler.load(compiler.MANIFEST)
    paths = [Path(__file__).resolve(), Path(generation.__file__), Path(compiler.__file__),
             Path(ranked.__file__), compiler.MANIFEST, CLARIFICATION / "report.json", CLARIFICATION / "guard.json",
             *(HERE / specs[key]["file"] for key in ROOTS.values()), *ranked.FILES]
    return {str(p.relative_to(HERE)): sha256(p.read_bytes()).hexdigest() for p in paths}


@contextmanager
def scenario():
    with patch.object(generation, "suite", new=suite), patch.object(generation, "sources", new=sources), \
         patch.object(generation, "WORLDS", new=ROOTS), patch.object(generation, "CAP", new=CAP):
        yield


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("directory", type=Path)
    cli.add_argument("--model", type=Path, required=True)
    args = cli.parse_args()
    with scenario():
        generation.run(args.model, args.directory)
