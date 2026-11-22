"""Collect fixed-candidate logits on the official Afghanistan meeting views."""
import argparse
from importlib.util import module_from_spec, spec_from_file_location
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
fixture_path = HERE.parent / "replay.py"
spec = spec_from_file_location("documentary_2721_fixture", fixture_path)
fixture = module_from_spec(spec)
spec.loader.exec_module(fixture)
OPTIONS = {"process": "consultation", "fund": "unama-scope"}


def read(path):
    return json.loads(path.read_text())


def plan():
    inherited = scoped.plan()
    files = (Path(__file__), HERE / "protocol.md", HERE / "sources.py", HERE / "source-views.json",
             HERE.parent / "case.json", fixture_path, CLAIM / "plan.json", CLAIM / "collect_claims.py",
             CLAIM / "results.json")
    source = read(HERE / "source-views.json")
    rows = []
    for key, view in source["views"].items():
        for suffix, mapping in prior.MAPPINGS.items():
            rows.extend([
                prior.base.earlier.request(f"direct/{key}/{suffix}", 2,
                    prior.SYSTEM.replace("German desk", "source editor"), {
                        "first_message": view["text"],
                        "your_options": {letter: fixture.BLOCKS[OPTIONS[action]]["text"]
                                         for letter, action in mapping.items()},
                    }),
                prior.base.earlier.request(f"claim/{key}/{suffix}", 2, scoped.SYSTEM, {
                    "first_message": view["text"], "claim": scoped.HYPOTHESES["afghanistan"],
                    "responses": {letter: "supported" if action == "process" else "unsupported"
                                  for letter, action in mapping.items()},
                }),
            ])
    assert len(rows) == 24
    return {"requests": rows, "checkpoint_index_sha256": inherited["checkpoint_index_sha256"],
            "pins": {**inherited["pins"], **{
                str(path.relative_to(RUNS.parent)): collector.sha(path) for path in files}}}


def act(mode):
    expected = plan()
    if mode == "plan":
        return expected
    assert expected == read(HERE / "plan.json")
    original_run = collector.run

    def track(directory):
        with patch.object(collector, "roster", return_value={"afghanistan-2721-documentary-routing": fixture.CASE}):
            return original_run(directory)

    with patch.object(prior, "HERE", HERE), patch.object(prior, "OUT", OUT), patch.object(
        prior, "locked", return_value=expected
    ), patch.object(collector, "run", side_effect=track):
        return {"run": prior.run, "verify": prior.verify}[mode]()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("plan", "run", "verify"))
    args = parser.parse_args()
    output = act(args.mode)
    if args.mode != "run":
        print(json.dumps(output, ensure_ascii=False, indent=2))
