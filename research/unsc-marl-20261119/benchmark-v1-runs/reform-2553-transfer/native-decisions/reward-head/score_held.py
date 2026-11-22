"""Compare the frozen reward heads against same-information reference rules."""
from itertools import product
from pathlib import Path
from statistics import mean

import numpy as np

import held_native as held
import reward_head as head

HERE, READ = head.HERE, head.READ
ARCHIVED = head.PARTNER.parent / "private-results.json"
MODES = head.MODES
TOLERANCE = 1e-9


def close(a, b):
    return abs(a - b) < TOLERANCE


def summarize(rows):
    return {
        mode: {
            "mean_release": {
                arm: mean(row[mode][arm]["released"] for row in rows.values())
                for arm in next(iter(rows.values()))[mode]
            },
            "hybrid_contrasts": {
                control: compare(rows, mode, control)
                for control in ("raw_qwen", "typed_only", "strongest_fixed", "oracle")
            },
        }
        for mode in MODES
    }


def compare(rows, mode, control):
    differences = []
    for row in rows.values():
        values = row[mode]
        reference = (max(values[name]["released"] for name in ("fixed_legacy", "fixed_refreshed"))
                     if control == "strongest_fixed" else values[control]["released"])
        differences.append(values["hybrid"]["released"] - reference)
    return {"mean_delta": mean(differences),
            "wins": sum(d > TOLERANCE for d in differences),
            "losses": sum(d < -TOLERANCE for d in differences),
            "ties": sum(abs(d) <= TOLERANCE for d in differences)}


def run():
    fit = READ(HERE / "fit.json")
    training = {key: {mode: head.score(world, fit) for mode, world in modes.items()}
                for key, modes in head.training_set().items()}
    for row in READ(head.NATIVE / "scores.json")["scenarios"]:
        key = f'{row["order"]}/{row["receipt"]}'
        for mode, prior in row["results"].items():
            assert close(training[key][mode]["raw_qwen"]["released"], prior["mean"]["released"])
            assert close(training[key][mode]["oracle"]["released"], prior["prior_oracle"]["released"])

    outputs = READ(HERE / "verified.json")["outputs"]
    _, _, raw, edges, true = held.setup()
    local = [np.asarray(values) for values in raw]
    refs = {(r["staffing_probability"], r["rate"]): r["outcomes"] for r in READ(ARCHIVED)["rows"]}
    rows = {}
    for share, rate in product(held.SHARES, held.RATES):
        key = f"{share}/{rate}"
        modes = head.sample(local, edges, rate, share, true, outputs, key)
        rows[key] = {mode: head.score(world, fit) for mode, world in modes.items()}
        for mode, outcomes in rows[key].items():
            assert close(outcomes["oracle"]["released"], refs[share, rate][mode]["oracle"]["expected_release"])

    agrees = sum(
        held.native.LABELS["ab"][row["label"]] ==
        held.native.LABELS["ba"][outputs[key.removesuffix("/ab") + "/ba"]["label"]]
        for key, row in outputs.items() if key.endswith("/ab")
    )
    arms = next(iter(rows.values()))["content"]
    visibility_gains = {
        arm: mean(row["content"][arm]["released"] - row["arrival"][arm]["released"]
                  for row in rows.values())
        for arm in arms
    }
    pins = (Path(__file__), HERE / "verified.json", HERE / "plan.json", HERE / "fit.json", ARCHIVED)
    return {
        "held": rows, "training": training,
        "paired_label_order_agreements": agrees,
        "raw_calls": len(outputs),
        "label_counts": {letter: sum(row["label"] == letter for row in outputs.values()) for letter in "AB"},
        "held_policy_replays": sum(len(outcomes) for row in rows.values() for outcomes in row.values()),
        "summary": {"held": summarize(rows), "training": summarize(training),
                    "held_content_minus_arrival": visibility_gains},
        "sources": {str(path.relative_to(head.RUNS)): head.prior.digest(path) for path in pins},
    }


if __name__ == "__main__":
    head.native.frozen.emit(run())
