"""Replay native reply choices with complete and partial official statements."""
import argparse
import json
from pathlib import Path
import sys
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
RUNS = HERE.parents[1]
CLAIM = RUNS / "claim-scoped-routing"
OUT = HERE / "evidence"
sys.path.insert(0, str(CLAIM))
import collect_claims as scoped

prior = scoped.prior
collector = scoped.collector


def read(path):
    return json.loads(path.read_text())


def plan():
    base = scoped.plan()
    files = (Path(__file__), HERE / "protocol.md", HERE / "sources.py", HERE / "source-views.json",
             CLAIM / "collect_claims.py", CLAIM / "plan.json", CLAIM / "results.json")
    source = read(HERE / "source-views.json")
    rows = []
    for view, row in source["views"].items():
        for suffix, mapping in prior.MAPPINGS.items():
            rows.extend([
                prior.base.earlier.request(f"direct/{view}/{suffix}", 2, prior.SYSTEM, {
                    "first_message": row["text"], "your_options": {label: prior.OPTIONS[action]
                                                                   for label, action in mapping.items()},
                }),
                prior.base.earlier.request(f"claim/{view}/{suffix}", 2, scoped.SYSTEM, {
                    "first_message": row["text"], "claim": scoped.HYPOTHESES["reform"],
                    "responses": {letter: "supported" if action == "process" else "unsupported"
                                  for letter, action in mapping.items()},
                }),
            ])
    assert len(rows) == 24
    return {"requests": rows, "checkpoint_index_sha256": base["checkpoint_index_sha256"],
            "pins": {**base["pins"], **{str(p.relative_to(RUNS.parent)): collector.sha(p) for p in files}}}


def act(mode):
    spec = plan()
    if mode == "plan":
        return spec
    assert spec == read(HERE / "plan.json")
    original_run = collector.run

    def track(directory):
        with patch.object(collector, "roster", return_value={"reform-2553-documentary-routing": prior.previous.CASE}):
            return original_run(directory)

    with patch.object(prior, "HERE", HERE), patch.object(prior, "OUT", OUT), patch.object(
        prior, "locked", return_value=spec
    ), patch.object(collector, "run", side_effect=track):
        return {"run": prior.run, "verify": prior.verify}[mode]()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("plan", "run", "verify"))
    mode = parser.parse_args().mode
    result = act(mode)
    if mode != "run":
        print(json.dumps(result, indent=2, ensure_ascii=False))
