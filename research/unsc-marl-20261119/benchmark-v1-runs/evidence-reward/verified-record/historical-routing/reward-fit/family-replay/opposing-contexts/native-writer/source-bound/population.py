"""Evaluate the original dense route over all modeled UNIFIL receipt states."""
import numpy as np

import bound_writer as b

n, e, old = b.n, b.e, b.n.matched


def run():
    reviewed = n.read(b.HERE / "results.json")["records"]
    points = np.array([reviewed[str(mask)]["released_70"] for mask in range(8)])
    archived = old.data.banks()["unifil"]
    estimate = old.data.singleton(archived)
    coordinates = tuple(archived[k] for k in (0, 1, 2, 4))
    parameters = tuple([np.array(a) for a in e.read(path)["parameters"]] for path in (
        old.HERE.parents[1] / "fit.json", old.HERE.parent / "sparse-results.json"))
    opener_params = e.read(old.o.replan.study.OLD)["training"]["budget_fit"]
    result = {}
    for name, prior in old.o.R.TEST_PRIORS.items():
        opening = old.o.replan.study.opening(estimate, prior, opener_params)
        _, policies, values, mass = old.selector.choose(coordinates, opening, prior, parameters)
        eligible = [p for p in policies if values[p]["released"] >= values["quiet"]["released"] - 1e-10]
        selection = max(eligible, key=lambda arm: (values[arm]["net"], arm == "quiet"))
        frozen = {arm: old.o.measure(points, mass, prior, opening, policies[arm])
                  for arm in ("dense", "sparse", selection)}
        controls = old.o.controls(points, mass, prior, opening)
        fixed = max(value["net"] for key, value in controls.items() if key != "exact_ask_reply")
        assert all(row["net"] <= controls["exact_ask_reply"]["net"] + 1e-10 for row in frozen.values())
        result[name] = {"original_selector": selection, "frozen": frozen, "exact_controls": controls,
                        "dense_margin_over_best_fixed": float(frozen["dense"]["net"] - fixed)}
    return {"bank": points.tolist(), "conditioned_on_known_inventory_laws": result}


if __name__ == "__main__":
    e.emit(run())
