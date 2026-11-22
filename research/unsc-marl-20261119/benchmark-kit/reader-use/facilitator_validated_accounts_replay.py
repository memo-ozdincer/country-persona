"""Replay the measured writer under the same inventories and transport."""
import argparse
from hashlib import sha256
import json
from pathlib import Path

import numpy as np

import facilitator_fixed_public_bank_score as prior
import facilitator_validated_accounts as study

plan = prior.plan


def run(scores):
    bank = np.array(scores["released_bank"])
    replay = plan.run(scores)
    controls = prior.controls(scores, replay)
    values = {key: {"source_only_ready": case["fields"] == ["supported"] * 3,
                    "absent_field": case["fields"][1] if key.endswith("/withheld") else None}
              for key, case in scores["witnesses"].items()}
    previous = json.loads((study.fixed.EVIDENCE / "results.json").read_text())
    edges = [(a, a | i) for a in range(8) for i in (1, 2, 4) if not a & i]
    edge_changes = [{"before": a, "after": b, "source_validated": int(bank[b] - bank[a]),
                     "earlier": previous["released_bank"][b] - previous["released_bank"][a]}
                    for a, b in edges]
    files = (Path(__file__), Path(study.__file__), Path(prior.__file__), Path(plan.__file__),
             study.fixed.EVIDENCE / "results.json")
    return {"checks": values, "release_edges": edge_changes, "controls": controls, "paths": replay,
            "sha256": {str(p.relative_to(study.HERE)) if p.is_absolute() else p.name:
                       sha256(p.read_bytes()).hexdigest() for p in files}}


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("scores", type=Path)
    args = cli.parse_args()
    print(json.dumps(run(json.loads(args.scores.read_text())), indent=2))
