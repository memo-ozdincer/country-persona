"""Transfer a frozen documentary team across archived record banks."""
from hashlib import sha256
import json
from pathlib import Path
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import joint_fit as training
import prune
import objective as o

e, R = o.e, o.R
READER = o.replan.h.ARCHIVE.parent
KIT = READER.parent
FILES = {
    "unifil": KIT / "evidence/unifil-final-transfer/verified-transport.json",
    "myanmar": KIT / "evidence/myanmar-sponsorship-probe/score.json",
    "modular": READER / "facilitator-modular-record-evidence/complete-sentences.json",
}


def banks():
    unifil = e.read(FILES["unifil"])["bank"]
    myanmar = e.read(FILES["myanmar"])
    result = {"unifil": [unifil[f"team-{mask}"]["release_points"] for mask in range(8)],
              "myanmar": myanmar["revised_points"]}
    assert result["myanmar"] == [row["points"] for row in myanmar["records"]]
    for name, case in e.read(FILES["modular"])["results"].items():
        result[name] = [case["records"][f"normalized/{mask}"]["guarded_points"] for mask in range(8)]
    assert set(result) == {"unifil", "myanmar", "unama", "emergency"}
    assert all(len(points) == 8 and all(0 <= p <= 70 for p in points) for points in result.values())
    return {key: np.array(values, dtype=float) for key, values in result.items()}


def singleton(points):
    base = points[0]
    weights = points[[1, 2, 4]] - base
    mask = np.arange(8)[:, None] & np.array([1, 2, 4])
    estimated = np.minimum(70, base + (mask != 0) @ weights)
    assert estimated[[0, 1, 2, 4]].tolist() == points[[0, 1, 2, 4]].tolist()
    return estimated


def learned_maps(points, mass, params, law, openers, with_pruning):
    q, response = training.paired(points, mass, params)
    if with_pruning:
        old = prune.improve(points, law, openers, mass, params, True)
        q = q.copy()
        q[old["removed_states"]] = 0
        response = training.paired_quiet(points, mass, params, q)
    return q, response


def run():
    params_path = HERE.parent / "fit.json"
    source = e.read(params_path)
    params = [np.array(x) for x in source["parameters"]]
    study = o.replan.study
    original = e.read(study.OLD)["training"]["budget_fit"]
    output = {}
    for name, actual in banks().items():
        estimate = singleton(actual)
        comparisons = {}
        for law_id, law in R.TEST_PRIORS.items():
            openers = study.opening(estimate, law, original)
            mass = o.opening(*openers, law)
            policies = {
                "singletons_unpruned": learned_maps(estimate, mass, params, law, openers, False),
                "singletons_pruned": learned_maps(estimate, mass, params, law, openers, True),
                "full_unpruned": learned_maps(actual, mass, params, law, openers, False),
                "full_pruned": learned_maps(actual, mass, params, law, openers, True),
            }
            policies["singletons_exact_ask"] = o.exact_parts(mass, estimate)["exact_ask_reply"]
            comparisons[law_id] = {key: o.measure(actual, mass, law, openers, pair)
                                  for key, pair in policies.items()} | o.controls(actual, mass, law, openers)
            ceiling = comparisons[law_id]["exact_ask_reply"]["net"]
            assert all(row["net"] <= ceiling + 1e-10 for row in comparisons[law_id].values())
        output[name] = {"scores": actual.tolist(), "singleton_estimate": estimate.tolist(),
                        "max_estimation_error": float(np.max(np.abs(actual - estimate))), "conditions": comparisons}
    pins = (Path(__file__), HERE / "protocol.md", params_path, Path(o.__file__), Path(prune.__file__), *FILES.values())
    return {"dockets": output, "sha256": {path.name: sha256(path.read_bytes()).hexdigest() for path in pins}}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
