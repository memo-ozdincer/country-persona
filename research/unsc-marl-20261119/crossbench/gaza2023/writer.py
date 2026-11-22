"""Generate a common final-record bank for the focal routing benchmark."""
import argparse
import json
from pathlib import Path
import sys
from unittest.mock import patch

import routing

HERE = Path(__file__).resolve().parent
KIT = HERE.parents[1] / "benchmark-kit"
sys.path.insert(0, str(KIT / "validity-audit"))

import routing_climate_live_exchange as replay

runner, read, digest = replay.runner, replay.read, replay.digest
MODEL = KIT / "evidence/climate2021-factored-reply/launch.json"
GUIDE = (
    "Write a factual supplement of at most 85 words for the assigned focus, using the permitted focus evidence. "
    "The public record is common and already written. Preserve proposal versus adoption, sequence, author, speaker "
    "capacity, and exact restrictions where the evidence supports them. If only the focal slip is available, "
    "record what it supports and stop. Cover the supplied criteria without inventing a missing fact. "
    "Output only the supplement."
)


def requests():
    task = routing.load()
    for focus in task["focuses"]:
        for backup in (False, True):
            data = {"public_record": task["public_record"], "focal_slip": focus["requester_card"],
                    "coverage": [focus["requester_criterion"]]}
            if backup:
                data["archival_backup"] = focus["backup"]
                data["coverage"] += focus["backup_criteria"]
            fields = [f"{focus['id']}/slip"]
            if backup:
                fields.append(f"{focus['id']}/backup")
            yield replay.request(f"{focus['id']}/{'matched' if backup else 'slip'}", 160, GUIDE, data, fields)


def episode(generate):
    return [{"family": routing.load()["id"], "final": generate(list(requests()))}]


def locks():
    paths = (HERE / "task.json", HERE / "accession.json", HERE / "routing-results.json",
             HERE / "routing-fit.json", MODEL, Path(runner.__file__), Path(__file__))
    return {p.name: digest(p) for p in paths}


def run(directory):
    with patch.object(runner, "episode", episode), patch.object(runner, "locks", locks):
        runner.run(Path(read(MODEL)["model"]), directory)


def verify(directory):
    with patch.object(replay, "episode", episode), patch.object(replay, "locks", locks):
        return replay.verify(directory)


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("mode", choices=("run", "verify"))
    cli.add_argument("directory", type=Path)
    args = cli.parse_args()
    if args.mode == "run":
        run(args.directory)
    else:
        print(json.dumps({key: {"ended": row["ended"], "output": row["output"]}
                          for key, row in verify(args.directory).items()}, ensure_ascii=False, indent=2))
