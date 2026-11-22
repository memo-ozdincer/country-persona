"""Replay a two-label agreement guard without changing stored model replies."""
import json
import runpy
import sys
from unittest.mock import patch

import numpy as np

import wording

fit = wording.transfer.fit


def components(outputs, key):
    a = outputs[f"{key}/ab"]["logits"]
    b = outputs[f"{key}/ba"]["logits"]
    return [a["A"]-a["B"], b["B"]-b["A"]]


def guarded(outputs, key):
    return min(components(outputs, key)) if key.startswith("2739/early/") else fit.margin(outputs, key)


def donor_sensitivity():
    donor = wording.transfer.DONOR
    sys.path.insert(0, str(donor))
    try:
        fit_donor = runpy.run_path(str(donor/"fit_delisting.py"))
    finally:
        sys.path.pop(0)
    case = wording.read(donor/"case.json")
    original = wording.read(donor/"results.json")
    outputs = wording.read(donor/"verified.json")["outputs"]
    bank = fit_donor["bank"]
    with patch.dict(bank.__globals__, {"margin": lambda rows, key: min(components(rows, key))}):
        _, audited, _, records, _ = bank(case,outputs)
    team = fit_donor["team"]
    policies = [tuple(np.array(original[key][-1][name]) for name in ("sender", "receiver"))
                for key in ("history", "sampled_history")]
    with patch.object(team, "PRIVATE", {"2664": ("full", "diversion", "request-only"),
                                        "2744": tuple(case["early"])}):
        score = fit_donor["learner"].fit.compare(audited,*policies)["mean_utility"]["2744"]
    return {"prior": original["native"]["mean_utility"]["2744"], "guarded": score,
            "guarded_records": {key: row["audited"] for key,row in records.items()}}


def run():
    spec = wording.plan()
    assert spec == wording.read(wording.HERE/"plan.json")
    fresh = wording.read(wording.HERE/"verified.json")["outputs"]
    trace = {
        key: {name: components(fresh, prefix+key)
              for name,prefix in (("original", "2739/early/"), ("updated", "updated/"))}
        for key in wording.PARAPHRASES
    }
    with patch.dict(fit.bank.__globals__, {"margin": guarded}):
        scored = wording.evaluate(spec)
    archives = {}
    paths = (wording.source, wording.transfer.DONOR)
    for path in paths:
        outcomes = wording.read(path/"verified.json")["outputs"]
        keys = [key.removesuffix("/ab") for key in outcomes if key.endswith("/ab")]
        changed = [key for key in keys if (fit.margin(outcomes,key)>0) != (min(components(outcomes,key))>0)]
        archives[path.name] = {"pairs": len(keys), "acceptance_changes": changed}
    return {"orientation_margins": trace, "prior_bank_sensitivity": archives, "replay": scored,
            "donor_policy_sensitivity": donor_sensitivity()}


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, indent=2))
