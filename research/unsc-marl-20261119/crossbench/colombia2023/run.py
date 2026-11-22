"""Matched open-text drafting and revision on the Colombia verification docket."""
import argparse
import json
from pathlib import Path
import sys
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "benchmark-kit/validity-audit"))
import source_record_run as runner
import source_record_sudan as replay
import source_record_episode as protocol

CASE = HERE / "case.json"
ARMS = protocol.ARMS


def locks():
    return {f.name: runner.digest(f) for f in (CASE, Path(__file__).resolve(), Path(runner.__file__),
                                               Path(replay.__file__), Path(protocol.__file__))}


def episode(generate):
    case = json.loads(CASE.read_text())
    name = case["family"]
    public = case["public"]
    roles = tuple(case["roles"])
    individual = tuple({**public, **case["roles"][role]} for role in roles)
    full = {key: value for deck in individual for key, value in deck.items()}

    def call(label, role, cards, drafts, task, cap):
        return {"id": f"{name}/{label}", "evidence_ids": list(cards), "seen": [d["id"] for d in drafts], "cap": cap,
                "messages": [{"role": "system", "content": f"You are {role} in a retrospective drafting exercise. "
                              "The provided dated sources are the sole factual authority. Working notes are provisional."},
                             {"role": "user", "content": json.dumps({"task": task, "sources": cards,
                                      "working_notes": [d["output"] for d in drafts]}, ensure_ascii=False)}]}

    first = ("Write two source-cited notes for the chair on your assigned part of the record. Include one distinction "
             "or condition a drafter could otherwise lose. Treat unresolved authority as unresolved.")
    opening = [call(f"common/opening_{i}", f"the {role}", individual[i], [], first, 112)
               for i, role in enumerate(roles)]
    solo_tasks = [call(f"pooled_solo/opening_{i}", "a single historical analyst", full, [],
                       f"Focus this pass on the {role} area. {first}", 112) for i, role in enumerate(roles)]
    initial = generate(opening + solo_tasks)
    revisions = []
    for arm in ARMS:
        solo = arm == "pooled_solo"
        plans = solo_tasks if solo else opening
        for i, role in enumerate(roles):
            visible = [initial[plans[i]["id"]]]
            if arm != "independent_drafts":
                visible.append(initial[plans[1-i]["id"]])
            role_name = "a single historical analyst" if solo else f"the {role}"
            task = (f"Focus on the {role} area in two compact source-cited notes. Revise your note to preserve "
                    "the source's conditions. Resolve a discrepancy in the available notes if the dated source allows. "
                    "Identify any boundary that still needs verification. Cite documentary sources only.")
            revisions.append(call(f"{arm}/revision_{i}", role_name, full if solo else individual[i], visible, task, 112))
    revised = generate(revisions)
    task = ("Write the retrospective Council record in at most 185 words. Cover the draft and vote, the existing "
            "mandate extension, the prior and prospective ceasefire verification scopes and any conditions, the two "
            "statements from Brazil and the African members, and what shared ground those statements support. "
            "Distinguish statements from adopted authority and cite each factual sentence using bracketed source IDs.")
    chairs = [call(f"{arm}/chair", "the neutral Council record writer", full,
                   [revised[f"{name}/{arm}/revision_{i}"] for i in range(2)], task, 268) for arm in ARMS]
    return [{"family": name, "openings": initial, "revisions": revised, "final": generate(chairs)}]


def preflight():
    def mock(batch):
        return {row["id"]: {**row, "output": row["id"]} for row in batch}
    outcome, = episode(mock)
    for i in range(2):
        revisions = outcome["revisions"]
        get = lambda arm: revisions[f"{outcome['family']}/{arm}/revision_{i}"]
        first, peer = get("independent_drafts"), get("interactive")
        assert first["seen"] == peer["seen"][:1] and len(peer["seen"]) == 2
        assert first["evidence_ids"] == peer["evidence_ids"]
    assert len({tuple(row["evidence_ids"]) for row in outcome["final"].values()}) == 1
    assert sum(len(rows) for key, rows in outcome.items() if key != "family") == 13
    return {"calls": 13, "calls_per_arm": 5, "ceiling_per_arm": 716}


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("mode", choices=("check", "run", "replay"))
    cli.add_argument("directory", type=Path, nargs="?")
    cli.add_argument("--model", type=Path)
    args = cli.parse_args()
    if args.mode == "check":
        print(json.dumps(preflight(), indent=2))
    elif args.mode == "run":
        preflight()
        with patch.multiple(runner, episode=episode, locks=locks):
            runner.run(args.model, args.directory)
    else:
        with patch.multiple(replay, episode=episode, locks=locks):
            print(json.dumps(replay.replay(args.directory), indent=2))
