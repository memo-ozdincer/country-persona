"""Replay the Resolution 2664 append writer with Resolution 2739 source cards."""
import argparse
from importlib.util import module_from_spec, spec_from_file_location
import json
from pathlib import Path
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
RUNS = HERE.parents[1]
OUT = HERE / "evidence"
PREVIOUS = RUNS / "humanitarian-2664-admission/source-preserving"
CASE = json.loads((HERE.parent / "docket.json").read_text())
CARDS = {row["id"]: row["text"] for row in CASE["public"] + [block for desk in CASE["owned"] for block in desk]}
ORDERS = {
    "none": (), "sponsors": ("sponsors",), "algeria": ("algeria",),
    "sponsors-first": ("sponsors", "algeria"), "algeria-first": ("algeria", "sponsors"),
    "action-first": ("action", "algeria"), "action-second": ("algeria", "action"),
}
WIRE_KIND = {"sponsors": "sponsors", "algeria": "algeria", "action": "adopted-action"}


def load(name, path):
    spec = spec_from_file_location(name, path)
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


base = load("prior_append_writer", PREVIOUS / "study.py")
TASK = (base.TASK.replace("adopted safeguards and the national assessment",
                          "co-sponsors' rationale and Algeria's assessment")
        .replace("adopted oversight and the national assessment", "delegations' reporting positions"))
assert TASK != base.TASK


def plan():
    paths = (Path(__file__), HERE / "protocol.md", HERE.parent / "docket.json",
             HERE.parent / "anchor.json", HERE.parent / "provenance.json",
             HERE.parent / "correction-bank/chair-scope/source_bound.py",
             PREVIOUS / "study.py", PREVIOUS / "plan.json", PREVIOUS / "scores.json",
             Path(base.collector.__file__), base.RELEASE / "release.json")
    assert base.read(PREVIOUS / "plan.json")["requests"]["india-first"]["max_output_tokens"] == 85
    return {
        "pins": {str(p.relative_to(RUNS.parent)): base.collector.sha(p) for p in paths},
        "checkpoint_index_sha256": base.collector.sha(base.collector.MODEL / "model.safetensors.index.json"),
        "requests": {
            name: {"id": name, "max_output_tokens": 85, "messages": [
                {"role": "system", "content": TASK},
                {"role": "user", "content": json.dumps({"delivered": [
                    {"kind": WIRE_KIND[key], "text": CARDS[key]} for key in order
                ]}, ensure_ascii=False)},
            ]} for name, order in ORDERS.items()
        },
    }


def locked():
    spec = plan()
    assert spec == base.read(HERE / "plan.json")
    return spec


def act(mode):
    with patch.object(base, "HERE", HERE), patch.object(base, "OUT", OUT), patch.object(
        base, "locked", locked
    ), patch.object(base.collector, "roster", return_value={"reporting-2739": CASE}):
        # The base collector sets its own roster for generation, so use its
        # generic collect function directly with this docket's metadata.
        if mode == "verify":
            return base.verify()
        assert locked() == base.read(HERE / "plan.json")
        with patch.object(base.collector, "HERE", HERE), patch.object(
            base.collector.suite.e, "HERE", base.RELEASE
        ), patch.object(base.collector.suite, "collect", base.collect):
            base.collector.run(OUT)
    return None


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("plan", "run", "verify"))
    mode = parser.parse_args().mode
    if mode == "run":
        act(mode)
    else:
        print(json.dumps(plan() if mode == "plan" else act(mode), ensure_ascii=False, indent=2))
