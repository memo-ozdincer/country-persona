"""Validate final-review spans and summarize all three matched arms."""
import argparse
import json
from pathlib import Path
import sys

from deck import prepare
from run import ROOT

sys.path.insert(0, str(ROOT.parent / "judge"))
from score import by_id, score


def evaluate(run, path):
    deck, keys = prepare(run)
    judged = by_id(json.loads(path.read_text())["verdicts"])
    assert judged.keys() == keys.keys()
    results = {}
    for item in deck:
        id_ = item["id"]
        meta = keys[id_]
        scored = score(item, judged[id_])
        results.setdefault(meta["variant"], {})[meta["arm"]] = {
            "id": id_, "semantic": scored["final"], "guard": scored["guard"],
            "semantic_strict": scored["strict"],
            "criteria": {r["id"]: r["status"] for r in judged[id_]["units"]},
        }
    deltas = {}
    for variant, arms in results.items():
        a, b = (arms[arm]["semantic"] for arm in ("peer", "solo"))
        deltas[variant] = [a["lower"] - b["upper"], a["upper"] - b["lower"]]
    return {"results": results, "peer_minus_solo_70_point_bounds": deltas}


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("run", type=Path)
    cli.add_argument("judgments", type=Path)
    args = cli.parse_args()
    print(json.dumps(evaluate(args.run, args.judgments), indent=2))
