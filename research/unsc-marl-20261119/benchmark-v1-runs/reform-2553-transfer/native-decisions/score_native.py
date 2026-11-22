"""Dispatch native and fixed decision tables through the same source-valued channel."""
from itertools import product
import json
from pathlib import Path
from statistics import mean

import numpy as np

from live_choices import HERE, PARENT, LABELS, RATES, SHARE, case, prior, READ, frozen

MODES = ("content", "arrival", "none")
DECODERS = ("mean", "ab", "ba", "consensus")


def decode(first, second, fallback):
    rows = (first, second)
    predictions = {mapping: int(LABELS[mapping][row["label"]]) - 1
                   for mapping, row in zip(LABELS, rows, strict=True)}
    margins = {}
    for mapping, row in zip(LABELS, rows, strict=True):
        lookup = {card: letter for letter, card in LABELS[mapping].items()}
        margins[mapping] = row["logits"][lookup["1"]] - row["logits"][lookup["2"]]
    combined = sum(margins.values()) / 2
    selected = fallback if combined == 0 else int(combined < 0)
    agrees = predictions["ab"] == predictions["ba"]
    consensus = predictions["ab"] if agrees else fallback
    return {"actions": predictions | {"mean": selected, "consensus": consensus},
            "mapped_margin_1_over_2": margins, "label_agreement": agrees}


def dispatch(distribution, scene, outcomes, view, a, c):
    assert all(x in (0, 1) for x in a) and c in (0, 1)
    public = outcomes[(0, 0, 0)][0]
    direct = float(sum(distribution[b, mask] * outcomes[(a[view[b, mask]], b, c)][mask]
                       for b, mask in product(range(2), range(8))))
    check = case.private.expected(scene["returns"], distribution, view, np.asarray(a), c) + public
    assert abs(check - direct) < 1e-9
    return {"released": direct, "later_by_view": list(a), "third": c}


def run():
    evidence = READ(HERE / "verified.json")["outputs"]
    bank = READ(PARENT / "results.json")["orders"]
    repaired = READ(PARENT / "component.json")["orders"]
    all_rows, all_decodes = [], {}
    for order, permutation in case.ORDERS.items():
        _, local, edges, _, true = case.setup(permutation)
        for rate in RATES:
            label = f"{order}/{rate}"
            saved, = [r for r in bank[order]["forced_private_inventory"]
                      if r["receipt"] == rate and r["first_card_probability"] == SHARE]
            selected, = [r for r in repaired[order]["rows"] if r["p"] == rate and r["share"] == SHARE]
            scene = case.learned.features(case.COUNTS, case.CAPS, local, edges, (rate,) * 3, true)
            p = np.array([SHARE, 1. - SHARE])[:, None] * scene["mask_probabilities"][None, :]
            assert abs(p.sum() - 1) < 1e-9
            obs = scene["observe"]
            views = {"content": (obs, ("absent", "card1", "card2")),
                     "arrival": ((obs > 0).astype(int), ("absent", "arrived")),
                     "none": (np.zeros_like(obs), ("none",))}
            local_pick = [int(row.argmax()) for row in local]
            decoded = {}
            for view in ("absent", "card1", "card2", "arrived", "none", "independent"):
                decoded[view] = decode(evidence[f"{label}/{view}/ab"], evidence[f"{label}/{view}/ba"],
                                       local_pick[2 if view == "independent" else 0])
            all_decodes[label] = decoded
            results = {}
            for mode, (obs_map, names) in views.items():
                runs = {}
                for reader in DECODERS:
                    a = [decoded[obs_]["actions"][reader] for obs_ in names]
                    c = decoded["independent"]["actions"][reader]
                    runs[reader] = dispatch(p, scene, true, obs_map, a, c)
                for arm, ref in saved["outcomes"][mode].items():
                    reference = dispatch(p, scene, true, obs_map, ref["by_view"], ref["third"])
                    assert abs(reference["released"] - ref["released"]) < 1e-9
                    assert all(val["released"] <= saved["outcomes"][mode]["oracle"]["released"] + 1e-9
                               for val in runs.values())
                    runs["prior_" + arm] = reference
                if mode == "content":
                    a_ref, c_ref = selected["policies"]["later_then_third"]
                    best = dispatch(p, scene, true, obs_map, a_ref, c_ref)
                    assert abs(best["released"] - saved["outcomes"][mode]["oracle"]["released"]) < 1e-9
                    runs["native_later_with_planned_third"] = dispatch(
                        p, scene, true, obs_map, runs["mean"]["later_by_view"], c_ref)
                    runs["planned_later_with_native_third"] = dispatch(
                        p, scene, true, obs_map, a_ref, runs["mean"]["third"])
                results[mode] = runs
            all_rows.append({"order": order, "receipt": rate, "results": results})
    assert set(MODES) == set(all_rows[0]["results"])
    stats = {}
    for mode in MODES:
        stats[mode] = {arm: mean(row["results"][mode][arm]["released"] for row in all_rows)
                       for arm in all_rows[0]["results"][mode]}
    return {"scenarios": all_rows, "decodes": all_decodes, "means": stats,
            "label_order_agreements": sum(row["label_agreement"] for unit in all_decodes.values() for row in unit.values()),
            "independent_dispatch_checks": sum(len(values) for row in all_rows for values in row["results"].values()),
            "sha256": {p.name: prior.digest(p) for p in (Path(__file__), HERE / "verified.json",
                       HERE / "plan.json", PARENT / "results.json", PARENT / "component.json")}}


if __name__ == "__main__":
    frozen.emit(run())
