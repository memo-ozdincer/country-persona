"""Write and score the eight Jerusalem receipt conditions with the frozen Gaza writer."""
import argparse
from itertools import batched
import json
from pathlib import Path
from unittest.mock import patch

import numpy as np

import language_partner as partner
import transfer

HERE = partner.HERE
writer = partner.writer


def requests():
    task = partner.load()
    for focus in task["focuses"]:
        for matching in (False, True):
            payload = {"public_record": task["public_record"], "focal_slip": focus["slip"],
                       "coverage": focus["criteria"] if matching else focus["criteria"][:1]}
            fields = [f"{focus['id']}/slip"]
            if matching:
                payload["archival_backup"] = focus["backup"]
                fields.append(f"{focus['id']}/backup")
            yield partner.replay.request(f"{focus['id']}/{'matched' if matching else 'slip'}", 160,
                                         writer.GUIDE, payload, fields)


def episode(generate):
    rows = {}
    for group in batched(requests(), 4):
        rows.update(generate(list(group)))
    return [{"family": partner.load()["id"], "final": rows}]


def locks():
    return {**partner.locks(), "jerusalem_writer": partner.digest(Path(__file__)),
            "gaza_writer": partner.digest(Path(writer.__file__)),
            "factored_actions": partner.digest(HERE / "factored-evidence/actions.json"),
            "transferred_decoder": partner.digest(partner.GAZA / "factored-calibration-results.json")}


def run(directory):
    with patch.object(partner.runner, "episode", episode), patch.object(partner.runner, "locks", locks):
        partner.runner.run(Path(partner.read(writer.MODEL)["model"]), directory)


def verify(directory):
    with patch.object(partner.replay, "episode", episode), patch.object(partner.replay, "locks", locks):
        return partner.replay.verify(directory)


def score(directory):
    rows = verify(directory)
    annotation_path = directory / "annotations.json"
    labels = partner.read(annotation_path)["rows"]
    assert labels.keys() == rows.keys()
    review = {}
    for key, row in rows.items():
        ruling = labels[key]
        assert ruling["guard"] in {"clear", "uncertain", "failed"} and ruling["reason"]
        payload = json.loads(row["messages"][1]["content"])
        for i, evidence in ruling["met"].items():
            assert i in "01234" and evidence["record"] in row["output"] and evidence["record"]
            assert evidence["source"] and evidence["source"] in payload["focal_slip" if i == "0" else "archival_backup"]
        for evidence in ruling.get("issues", {}).values():
            assert evidence and evidence in row["output"]
        words = len(row["output"].split())
        raw = 35 + 7 * len(ruling["met"])
        clear = row["ended"] and words <= 85 and ruling["guard"] == "clear"
        review[key] = {"raw": raw, "strict_release": raw if clear else 0, "words": words,
                       "guard": ruling["guard"], "met": list(ruling["met"])}
    calibration = transfer.Calibration()
    calibration.points[:] = np.tile([42, 70], (4, 1))
    frozen = np.asarray(transfer.read("factored-calibration-results.json")["greedy_receiver_table"])
    desks = partner.read(HERE / "factored-evidence/actions.json")["desks"]
    replayed = {}
    for kind in ("raw", "strict_release"):
        points = np.array([[review[f"{focus['id']}/{receipt}"][kind] for receipt in ("slip", "matched")]
                           for focus in partner.load()["focuses"]])
        replayed[kind] = {"points": points.tolist(),
                          "desks": {name: transfer.score(actions, frozen, calibration, points)
                                    for name, actions in desks.items()}}
    return {"scope": "Same-assistant exact-span review of new frozen Qwen writer records. The learned and exact "
                     "decoders select against announced values. Actual raw and strict record credit is used only in replay.",
            "trace_sha256": partner.digest(directory / "transcript.jsonl"),
            "annotation_sha256": partner.digest(annotation_path), "records": review, "replays": replayed}


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("mode", choices=("run", "score"))
    cli.add_argument("directory", type=Path)
    args = cli.parse_args()
    if args.mode == "run":
        run(args.directory)
    else:
        print(json.dumps(score(args.directory), indent=2, ensure_ascii=False))
