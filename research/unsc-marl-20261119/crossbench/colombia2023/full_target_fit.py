"""Fit to complete delivery on written voting and replay on two archived record banks."""
import json
from pathlib import Path

import full_target_headroom as ceiling
import specialist_fit as specialist

HERE = specialist.HERE
roster = specialist.shift
relay = specialist.relay
optimizer = specialist.optimizer
VALUE = ceiling.RELEASE_VALUE
PARENT = HERE / "specialist-fit-results.json"
COLOMBIA = HERE / "field-update-evidence/results.json"


def lock():
    paths = (Path(__file__), Path(ceiling.__file__), Path(specialist.__file__), Path(optimizer.__file__),
             Path(roster.__file__), Path(relay.__file__), PARENT, ceiling.OBSERVED, COLOMBIA,
             ceiling.OBSERVED.parents[2] / "ftf2020/adaptive-align-results.json", HERE / "verified-transfer.json")
    return {str(p.resolve().relative_to(HERE.parent)): specialist.shift.runner.digest(p) for p in paths}


def summary(dist, target, anchor, ids, generated):
    metrics = {key: 0. for key in ("receipt", "release", "cost", "contacts", "record_points",
                                   "released_points", "partial_inclusive_release")}
    assert abs(sum(item[0] for item in dist.values()) - 1) < 1e-9
    for missing, (mass, fees, contacts) in dist.items():
        key = ",".join(sorted(ids[i] for i in set(target) - set(missing)))
        points, strict_packet = generated[key]
        metrics["receipt"] += mass * (not missing)
        metrics["release"] += mass * (not missing) * strict_packet
        metrics["partial_inclusive_release"] += mass * strict_packet
        metrics["cost"] += fees
        metrics["contacts"] += contacts
        metrics["record_points"] += mass * points
        metrics["released_points"] += mass * points * strict_packet
    metrics["strict_net"] = VALUE * metrics["release"] - metrics["cost"]
    return metrics


def replay(policies):
    unifil = roster.transfer.read(ceiling.OBSERVED)["packets"]
    colombia = roster.transfer.read(COLOMBIA)["composed"]["packets"]
    banks = {"unifil_fields": {k: (r["points"], r["releasable"]) for k, r in unifil["fields"].items()},
             "unifil_whole": {k: (r["points"], r["releasable"]) for k, r in unifil["whole"].items()},
             "colombia_selected_fields": {k: (r["points"], r["release"]) for k, r in colombia.items()}}
    datasets = {name: (ids, mapping) for name, ids, _, mapping in roster.datasets()}
    conditions = ("strong_specialist_B", "mislabelled_specialist_B", "separate_desk_specialties")
    all_results = {}
    for name, bank in banks.items():
        ids, mapping = datasets[name.split("_")[0]]
        contexts = {(r["anchor"], *r["other_cards"]): r for r in mapping["rows"]}
        results = {}
        for condition in conditions:
            rows = []
            for target, anchor in relay.SCENARIOS:
                needed = sorted(set(target) - {anchor})
                context = contexts[(ids[anchor], *(ids[i] for i in needed))]
                weight, expert, kind = roster.CONDITIONS[condition]
                prior = roster.distribution(needed, weight, expert, kind)
                hint = 1 - expert if kind == "wrong_hint" else expert
                packet = ",".join(sorted(ids[i] for i in target))
                enough = bank[packet][1]
                item = {}
                for label, (policy, canonical) in policies.items():
                    dist = roster.remap(policy, prior, target, anchor, context, (hint, 1 - hint), canonical)
                    item[label] = summary(dist, target, anchor, ids, bank)
                limit = ceiling.solve(target, anchor, prior, enough, True)
                for label, actual in item.items():
                    assert actual["strict_net"] <= limit["strict_net"] + 1e-9, (name, condition, target, label)
                rows.append({"target": packet, "anchor": ids[anchor], "policies": item,
                             "upper_bound": {key: limit[key] for key in ("full_target_release", "strict_net", "cost")}})
            results[condition] = {"mean": roster.transfer.mean([row["policies"] for row in rows]), "scenarios": rows,
                                  "oracle": {key: sum(row["upper_bound"][key] for row in rows) / len(rows)
                                             for key in rows[0]["upper_bound"]}}
        all_results[name] = results
    prior_evidence = roster.transfer.read(ceiling.OBSERVED)["routes"]
    for arm in ("whole", "fields"):
        fresh = all_results["unifil_" + arm]["strong_specialist_B"]["mean"]["raw_reward"]
        expected = prior_evidence[arm]["mean"]["joint"]
        for key, other in (("release", "full_target_release_probability"), ("cost", "cost"),
                           ("record_points", "record_points"), ("receipt", "complete_required_cards")):
            assert abs(fresh[key] - expected[other]) < 1e-9
    return all_results


def run():
    states, actions, outcomes, mass = specialist.batches()
    objective = outcomes.copy()
    objective[:, 2] = 35 + VALUE * outcomes[:, 1]
    history, trained = optimizer.fit(states, actions, objective, mass)
    p = trained["joint_learned"]
    original = roster.transfer.read(PARENT)
    raw = {roster.transfer.immutable(row["local_state"]): row["probabilities"] for row in original["policy"]}
    old = p.copy()
    for state, (offset, width) in states.items():
        old[offset:offset + width] = raw[state]
    train_metrics = {}
    for label, vector in (("raw_reward", old), ("full_delivery_reward", p)):
        train_metrics[label] = {"original_endpoint": optimizer.evaluate(vector, actions, outcomes, mass)["design_mixture"],
                                "strict_endpoint": optimizer.evaluate(vector, actions, objective, mass)["design_mixture"]}
    old_metrics = train_metrics["raw_reward"]["original_endpoint"]
    assert all(abs(value - original["trained_record"]["new"][key]) < 1e-9
               for key, value in old_metrics.items() if key != "record_reward")
    assert abs(history[-1]["record_reward"] - train_metrics["full_delivery_reward"]["strict_endpoint"]["record_reward"]) < 1e-9
    learned = {state: p[offset:offset + width].tolist() for state, (offset, width) in states.items()}
    routes = replay({"raw_reward": (raw, False), "full_delivery_reward": (learned, False),
                     "full_delivery_with_canonical_reply": (learned, True)})
    return {"scope": "One matched exact policy-gradient fit. Only the written-vote task supplies the reward. "
                     "Strict release on UNIFIL and Colombia is read from archived writer packets after fitting. "
                     "The oracle sees the roster prior, release feasibility and a reply-order control.",
            "locks": lock(), "updates": optimizer.STEPS, "full_delivery_value": VALUE,
            "training": {"history": history, "metrics": train_metrics,
                         "trajectory_rows": len(actions), "states": len(states)},
            "transfer": routes, "policy": [{"local_state": k, "probabilities": v} for k, v in learned.items()]}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
