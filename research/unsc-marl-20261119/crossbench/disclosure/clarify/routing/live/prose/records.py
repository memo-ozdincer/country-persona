"""Render the selected opening paths from model-inferred compatibility menus."""
import argparse
import json
from pathlib import Path

from study import CASES
from compose import compose


def recover(metrics):
    episodes = {}
    for family,variant,opening in CASES:
        for arm in ("script","learned"):
            path = f"{family}/{variant}/{''.join(opening)}/{arm}"
            row = metrics["paths"][path]["prose"]
            episodes[f"{family}/{variant}/{arm}"]={"claims":row["claims"],"readout":row["proof"]}
    return compose({"episodes":episodes})


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("metrics",type=Path)
    print(json.dumps(recover(json.loads(p.parse_args().metrics.read_text())),indent=2,ensure_ascii=False))
