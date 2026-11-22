"""Collect split source claims and replay the fixed documentary policies."""
import argparse
from copy import deepcopy
import json
from pathlib import Path
import runpy
import sys
from unittest.mock import patch

import numpy as np

HERE = Path(__file__).resolve().parent
RUNS = HERE.parent
PREVIOUS = RUNS / "delisting-to-reporting-transfer/wording"
sys.path.insert(0, str(PREVIOUS))
import wording

fit = wording.transfer.fit
cpu = wording.cpu
read = wording.read
DONOR = wording.transfer.DONOR
CLAIMS = {
    "2739": {
        "reporting": "Algeria said continued reporting on attacks helps keep the Council informed.",
        "abstention": "Algeria gave an implementation or self-defence concern as a reason for its abstention.",
    },
    "2744": {
        "timing": "The speaking delegation itself says a time-bound review of the Focal Point would have been useful.",
        "implementation": "The speaking delegation wants the continuous review provision implemented.",
    },
}


def references():
    previous = read(PREVIOUS/"plan.json")["requests"]
    old_donor = read(DONOR/"plan.json")["requests"]
    target = {}
    for request in previous:
        stem, order = request["id"].rsplit("/", 1)
        if stem == "2739/early/voted-only":
            continue
        target.setdefault(stem, {})[order] = request
    for order, request in target["updated/full"].items():
        changed = deepcopy(request)
        payload = json.loads(changed["messages"][1]["content"])
        payload["source_text"] = (
            "Algeria said the Secretary-General's monthly reports on attacks on commercial "
            "shipping were useful for keeping the Council informed."
        )
        changed["messages"][1]["content"] = json.dumps(payload, ensure_ascii=False)
        target.setdefault("foil/reporting-only", {})[order] = changed
    donor = {}
    for request in old_donor:
        stem, order = request["id"].rsplit("/", 1)
        if stem not in {f"early/{key}/review" for key in ("a3plus", "malta", "switzerland", "review-quoted")}:
            continue
        donor.setdefault(stem, {})[order] = request
    for order, request in donor["early/a3plus/review"].items():
        changed = deepcopy(request)
        payload = json.loads(changed["messages"][1]["content"])
        source = payload["source_text"]
        assert "urged effective implementation" in source
        payload["source_text"] = source.replace("urged effective implementation", "hoped for full implementation")
        changed["messages"][1]["content"] = json.dumps(payload, ensure_ascii=False)
        donor.setdefault("updated/a3plus/review", {})[order] = changed
    return {"2739": target, "2744": donor}


def plan():
    requests = []
    refs = references()
    expected = {"2739": ["2739/early/full", "updated/full"],
                "2744": ["early/a3plus/review", "updated/a3plus/review"]}
    for family, cards in refs.items():
        for key, pair in cards.items():
            for component, claim in CLAIMS[family].items():
                for order, request in pair.items():
                    row = deepcopy(request)
                    row["id"] = f"{family}/{key}/{component}/{order}"
                    payload = json.loads(row["messages"][1]["content"])
                    payload["proposition"] = claim
                    row["messages"][1]["content"] = json.dumps(payload, ensure_ascii=False)
                    requests.append(row)
    assert len(requests) == 44
    paths = (Path(__file__), HERE/"protocol.md", PREVIOUS/"plan.json", PREVIOUS/"wording.py",
             PREVIOUS/"verified.json", PREVIOUS.parent/"plan.json", DONOR/"plan.json",
             DONOR/"verified.json", DONOR/"results.json", DONOR/"fit_delisting.py",
             wording.source/"verified.json", wording.source/"fit.py", Path(cpu.__file__))
    return {"requests": requests, "keys": {k: list(v) for k,v in refs.items()}, "expected": expected,
            "checkpoint_index_sha256": read(DONOR/"plan.json")["checkpoint_index_sha256"],
            "pins": {str(path.relative_to(RUNS)): wording.transfer.digest(path) for path in paths}}


def target_replay(margins):
    canonical_outputs = wording.read(PREVIOUS/"verified.json")["outputs"]
    # Match the exact stored original/updated label pairs rather than
    # keying an inference on an evaluator's answer label.
    by_pair = {}
    for key in wording.PARAPHRASES:
        for stem in (f"2739/early/{key}", f"updated/{key}"):
            pair = tuple(canonical_outputs[f"{stem}/{order}"]["logits"] for order in ("ab", "ba"))
            by_pair[json.dumps(pair, sort_keys=True)] = margins.get(stem)

    def override(outputs, key):
        result = fit.margin(outputs, key)
        if not key.startswith("2739/early/"):
            return result
        pair = tuple(outputs[f"{key}/{order}"]["logits"] for order in ("ab", "ba"))
        value = by_pair[json.dumps(pair, sort_keys=True)]
        return result if value is None else value

    preflight = wording.plan()
    load = wording.read

    def wording_read(path):
        if path == PREVIOUS/"verified.json":
            return {"outputs": canonical_outputs}
        return load(path)

    with patch.object(wording, "read", side_effect=wording_read), patch.dict(
        fit.bank.__globals__, {"margin": override}
    ):
        return wording.evaluate(preflight)


def donor_replay(margins, use_hope=False):
    sys.path.insert(0, str(DONOR))
    try:
        donor = runpy.run_path(str(DONOR/"fit_delisting.py"))
    finally:
        sys.path.pop(0)
    original = read(DONOR/"results.json")
    source = read(DONOR/"verified.json")["outputs"]
    case = read(DONOR/"case.json")
    primary = "early/a3plus/review"

    def override(outputs, key):
        if use_hope and key == primary:
            return margins["updated/a3plus/review"]
        return margins[key] if key in margins else fit.margin(outputs, key)

    compiler = donor["bank"]
    with patch.dict(compiler.__globals__, {"margin": override}):
        _, bank, _, records, _ = compiler(case, source)
    policies = [tuple(np.array(original[name][-1][key]) for key in ("sender", "receiver"))
                for name in ("history", "sampled_history")]
    with patch.object(donor["team"], "PRIVATE", {"2664": ("full", "diversion", "request-only"),
                                                 "2744": tuple(case["early"])}):
        scored = donor["learner"].fit.compare(bank,*policies)["mean_utility"]["2744"]
    return {"utility": scored, "released_pairs": {key: row["audited"] for key,row in records.items()}}


def score(spec):
    outputs = read(HERE/"verified.json")["outputs"]
    assert set(outputs) == {row["id"] for row in spec["requests"]}
    components = {
        family: {key: {part: fit.margin(outputs, f"{family}/{key}/{part}") for part in CLAIMS[family]}
                 for key in keys}
        for family,keys in spec["keys"].items()
    }
    margins = {family: {key: min(parts.values()) for key,parts in cards.items()}
               for family,cards in components.items()}
    audit = {family: {key: {"predicted": score > 0, "expected": key in spec["expected"][family]}
                      for key,score in cards.items()}
             for family,cards in margins.items()}
    return {"components": components, "audit": audit, "target": target_replay(margins["2739"]),
            "donor": {"original": donor_replay(margins["2744"]),
                      "source_faithful": donor_replay(margins["2744"], use_hope=True)}}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("plan", "run", "verify", "score"))
    mode = parser.parse_args().mode
    spec = plan()
    if mode != "plan":
        assert spec == read(HERE/"plan.json")
    if mode in {"run", "verify"}:
        with patch.object(cpu, "HERE", HERE), patch.object(cpu, "OUT", HERE/"evidence"), patch.object(
            cpu, "locked", return_value=spec
        ):
            result = {"run": cpu.run, "verify": cpu.verify}[mode]()
    else:
        result = spec if mode == "plan" else score(spec)
    if mode != "run":
        print(json.dumps(result, ensure_ascii=False, indent=2))
