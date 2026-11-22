"""Compare an actual peer question, independent notes, and a pooled analyst."""
import argparse
import json
from pathlib import Path
from unittest.mock import patch

import run as parent

HERE = parent.HERE
runner = parent.runner
UNIFIL = HERE.parent / "unifil-record.json"
HAITI = HERE.parent / "haiti2023/case.json"
ARMS = ("independent", "interactive", "pooled", "source_relay")
FAMILY = "peer-question"
OPEN = ("Write a short evidence note from the first delegation's source. Use at most 46 words. "
        "Then ask the second desk one precise question about what can safely be said about shared ground or disagreement. "
        "Identify the source ID for the note. Do not answer the question with an inference about the second delegation.")
REPLY = ("Write one evidence note from the second delegation's source in at most 54 words. Include its source ID. "
         "Keep the stated reasons, qualifications, and institutional capacity. "
         "If a question is supplied, make sure your note addresses it when your source permits. "
         "Use the message to identify what needs checking. Treat only your documentary source as authority for the second delegation.")
WRITE = ("Write a retrospective Council record supplement in at most 140 words. The vote line is already recorded. "
         "Preserve the distinct mandates or terms stated in the public documentary cards. State both delegation accounts, giving their "
         "material qualifications and distinguishing limited common ground from views about the adopted text. Use source IDs. "
         "Use only facts in the documentary cards or sourced desk notes. Do not repeat a question or invent its answer.")


def fixtures():
    force = json.loads(UNIFIL.read_text())
    documents = {row["id"]: row["text"] for row in force["evidence"]}
    vote = documents.pop("vote")
    national = {key: documents.pop(key) for key in ("china", "brazil")}
    yield "unifil", vote, documents, national
    mission = json.loads(HAITI.read_text())
    documents = {key: row["card"] for key, row in mission["sources"].items()}
    national = {key: documents.pop(key) for key in ("CHINA", "A3")}
    yield "haiti", mission["public"], documents, national


def request(family, arm, stage, cap, task, role, public, local, seen):
    return {"id": f"{family}/{arm}/{stage}", "cap": cap, "evidence_ids": list(local),
            "seen": [row["id"] for row in seen], "messages": [
                {"role": "system", "content": f"You are {role} in a historical Council record exercise."},
                {"role": "user", "content": json.dumps({"task": task, "public_record": public,
                                                        "documentary_cards": local,
                                                        "working_notes": [row["output"] for row in seen]},
                                                       ensure_ascii=False)}]}


def episode(generate):
    cases = list(fixtures())
    opening_requests = []
    for family, vote, public, national in cases:
        a, b = national
        for arm in ("shared", "pooled"):
            local = {a: national[a]} if arm == "shared" else national
            role = "the first documentary desk" if arm == "shared" else "a single historical analyst"
            opening_requests.append(request(family, arm, "open", 84, f"First source [{a}]. Second source [{b}]. {OPEN}",
                                            role, vote, local, ()))
    opening = generate(opening_requests)
    replies = []
    for family, vote, public, national in cases:
        a, b = national
        for arm in ARMS[:3]:
            notes = (opening[f"{family}/shared/open"],) if arm == "interactive" else ()
            if arm == "pooled":
                notes = (opening[f"{family}/pooled/open"],)
            local = national if arm == "pooled" else {b: national[b]}
            role = "a single historical analyst" if arm == "pooled" else "the second documentary desk"
            replies.append(request(family, arm, "reply", 98, f"Second source [{b}]. {REPLY}", role, vote, local, notes))
    answered = generate(replies)
    writers = []
    for family, vote, public, national in cases:
        for arm in ARMS:
            local = public | national if arm == "source_relay" else public
            first = "pooled" if arm == "pooled" else "shared"
            notes = () if arm == "source_relay" else (opening[f"{family}/{first}/open"], answered[f"{family}/{arm}/reply"])
            writers.append(request(family, arm, "final", 222, WRITE, "the neutral archival chair", vote, local, notes))
    return [{"family": FAMILY, "open": opening, "reply": answered, "final": generate(writers)}]


def locks():
    paths = (Path(__file__), Path(runner.__file__), Path(parent.replay.__file__), UNIFIL, HAITI)
    return {p.name: runner.digest(p) for p in paths}


def mock(batch):
    return {r["id"]: r | {"output": r["id"]} for r in batch}


def check():
    dry, = episode(mock)
    assert len(dry["open"]) == 4 and len(dry["reply"]) == 6 and len(dry["final"]) == 8
    for family, *_ in fixtures():
        for stage, cap in (("reply", 98), ("final", 222)):
            control = dry[stage][f"{family}/independent/{stage}"]
            intervention = dry[stage][f"{family}/interactive/{stage}"]
            assert control["cap"] == intervention["cap"] == cap
            assert control["evidence_ids"] == intervention["evidence_ids"]
            left, right = (json.loads(row["messages"][-1]["content"]) for row in (control, intervention))
            assert {k: v for k, v in left.items() if k != "working_notes"} == {
                k: v for k, v in right.items() if k != "working_notes"}
            if stage == "reply":
                assert control["seen"] == [] and intervention["seen"] == [f"{family}/shared/open"]
            else:
                assert len(control["seen"]) == len(intervention["seen"]) == 2
                assert control["seen"][0] == intervention["seen"][0]


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("mode", choices=("run", "replay"))
    cli.add_argument("directory", type=Path)
    cli.add_argument("--model", type=Path)
    args = cli.parse_args()
    check()
    if args.mode == "run":
        with patch.multiple(runner, episode=episode, locks=locks):
            runner.run(args.model, args.directory)
    else:
        from peer_question_score import replay

        print(json.dumps({"exact_transcript_rows": len(replay(args.directory))}, indent=2))
