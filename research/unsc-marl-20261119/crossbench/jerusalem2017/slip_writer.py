"""Hold live replies fixed and remove the writer's redundant public paragraph."""
import argparse
import json
from pathlib import Path
from unittest.mock import patch

import live_protocol as live
import live_review as review

partner = live.partner
BASE = live.HERE / "live-evidence"


def requests(previous):
    for name, row in previous.items():
        if name.startswith("chair/"):
            data = json.loads(row["messages"][1]["content"])
            del data["public_record"]
            yield partner.replay.request(name, row["cap"], row["messages"][0]["content"], data, row["evidence_ids"])


def episode(previous):
    def play(generate):
        return [{"family": partner.load()["id"], "final": live.batches(generate, requests(previous))}]
    return play


def locks():
    return {**live.locks(), "intervention_script": partner.digest(Path(__file__)),
            "old_live_trace": partner.digest(BASE / "transcript.jsonl"),
            "old_live_review": partner.digest(BASE / "annotations.json")}


def run(directory):
    previous = live.verify(BASE)
    with patch.object(partner.runner, "episode", episode(previous)), patch.object(partner.runner, "locks", locks):
        partner.runner.run(Path(partner.read(partner.writer.MODEL)["model"]), directory)


def inputs(directory):
    previous = live.verify(BASE)
    with patch.object(partner.replay, "episode", episode(previous)), patch.object(partner.replay, "locks", locks):
        chairs = partner.replay.verify(directory)
    rows = {**previous, **chairs}
    return rows, partner.load(), live.decide(live.actions(rows))


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("mode", choices=("run", "score"))
    cli.add_argument("directory", type=Path)
    args = cli.parse_args()
    if args.mode == "run":
        run(args.directory)
    else:
        with patch.object(review, "inputs", inputs):
            print(json.dumps(review.review(args.directory), indent=2, ensure_ascii=False))
