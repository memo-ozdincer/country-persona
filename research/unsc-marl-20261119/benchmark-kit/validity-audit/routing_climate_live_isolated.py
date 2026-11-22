"""Write one national sentence per distinct admitted annex and assemble verbatim."""
import argparse
import json
from pathlib import Path
from unittest.mock import patch

import routing_climate_live_exchange as live

runner, read, digest = live.runner, live.read, live.digest
BASE = live.transfer.base.space.OUT / "climate2021-live-exchange"
GUIDE = (
    "Write one sentence about the delegation named in the note. Attribute its position explicitly. Include the main "
    "reason it gave, the forum it preferred or objected to if stated, and its preferred action and geographic scope. "
    "Use only the note. Write at most 36 words, with semicolons permitted if needed. Output only the sentence."
)


def locks():
    return {**live.locks(), "isolated_writer": digest(Path(__file__)),
            "live_trace": digest(BASE / "transcript.jsonl")}


def requests(previous):
    first = previous["note-russia-explanation"]
    note_id, note = live.admit_note(first, first["evidence_ids"][0])
    selected = {note_id: note}
    for arm in live.ARMS:
        entry = live.admit_note(previous[f"reply-{arm}"])
        if entry is not None:
            evidence_id, text = entry
            selected.setdefault(evidence_id, text)
    return [live.request(f"national-{field}", 80, GUIDE, {"admitted_note": text}, [field])
            for field, text in selected.items()]


def episode(previous):
    def play(generate):
        return [{"family": live.transfer.task()["id"], "final": generate(requests(previous))}]
    return play


def run(directory):
    previous = live.verify(BASE)
    with patch.object(runner, "episode", episode(previous)), patch.object(runner, "locks", locks):
        runner.run(Path(read(BASE / "launch.json")["model"]), directory)


def verify(directory):
    previous = live.verify(BASE)
    new_locks = locks()
    with patch.object(live, "episode", episode(previous)), patch.object(live, "locks", lambda: new_locks):
        isolated = live.verify(directory)
    for arm in live.ARMS:
        old = previous[f"chair-{arm}"]
        parts = [isolated[f"national-{field}"] for field in old["evidence_ids"]]
        previous[f"chair-{arm}"] = {
            **old, "output": " ".join(part["output"] for part in parts),
            "ended": all(part["ended"] and len(part["output"].split()) <= 36 for part in parts),
            "input_ids": [token for part in parts for token in part["input_ids"]],
            "output_ids": [token for part in parts for token in part["output_ids"]],
            "cap": sum(part["cap"] for part in parts),
        }
    return previous


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("mode", choices=("run", "verify"))
    cli.add_argument("directory", type=Path)
    args = cli.parse_args()
    if args.mode == "run":
        run(args.directory)
    else:
        rows = verify(args.directory)
        print(json.dumps({key: rows[key]["output"] for key in rows if key.startswith("chair-")}, indent=2))
