"""Build opaque final-review packets without changing output text."""
import argparse
import hashlib
import json
from pathlib import Path
import random
import sys

from run import FAMILY, ROOT, inputs

sys.path.insert(0, str(ROOT.parent / "judge"))
from score import request
from packets import packet


def prepare(run):
    metadata = json.loads((run / "complete.json").read_text())
    path = run / "transcript.jsonl"
    transcript = path.read_bytes()
    assert hashlib.sha256(transcript).hexdigest() == metadata["release_sha256"]
    archive = {r["id"]: r for line in transcript.splitlines() for r in [json.loads(line)]}
    data, _ = inputs()
    item = next(f for f in data["families"] if f["id"] == FAMILY)
    result, key = [], {}
    for variant in item["variants"]:
        reference = packet(item, variant, data["boundary"], "judge")
        for arm in ("solo", "peer", "analyst"):
            run_id = f"final-{arm}-{variant['id']}"
            opaque = "R-" + hashlib.sha256(f"review-261119::{run_id}".encode()).hexdigest()[:10]
            assert opaque not in key
            result.append(request({**reference, "id": opaque, "answer": archive[run_id]["output"]}))
            key[opaque] = {"arm": arm, "variant": variant["id"], "record": run_id}
    random.Random(261119).shuffle(result)
    return result, key


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("run", type=Path)
    cli.add_argument("output", type=Path)
    args = cli.parse_args()
    deck, key = prepare(args.run)
    args.output.mkdir()
    for name, payload in [("deck.json", deck), ("arm-key.json", key)]:
        (args.output / name).write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
