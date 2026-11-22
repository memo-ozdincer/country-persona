"""Check and score the source-section intervention against frozen inputs."""
import argparse
from hashlib import sha256
import json

from run_sections import EVIDENCE, FAMILY, HERE, live, pins, requests
from score_transfer import read_rows, score_batch


def masked(key):
    return sha256(("2719-source-sections/" + key).encode()).hexdigest()[:10]


def score():
    prompts, paths = live.plan()
    updated = requests()
    for initial, changed in zip(prompts, updated, strict=True):
        assert initial["id"] == changed["id"] and initial["cap"] == changed["cap"]
        assert initial["messages"][1:] == changed["messages"][1:]
    return score_batch(EVIDENCE, FAMILY, updated, pins(), paths, HERE, masked)


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("mode", choices=("deck", "score", "records"))
    mode = cli.parse_args().mode
    if mode == "score":
        result = score()
    else:
        rows = read_rows(EVIDENCE)
        result = ({key: live.load(live.PROTOCOL)["public"] + "\n\n" + row["output"] for key, row in rows.items()}
                  if mode == "records" else dict(sorted((masked(key), r["output"]) for key, r in rows.items())))
    print(json.dumps(result, ensure_ascii=False, indent=2))
