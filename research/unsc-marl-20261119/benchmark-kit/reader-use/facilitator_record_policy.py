"""Compare joint routing fits that differ only in how they reward the final brief."""
from collections import Counter, defaultdict
from hashlib import sha256
import json
from pathlib import Path

import numpy as np

import facilitator_event_transfer as transfer
import facilitator_fresh_briefs as dev

base = dev.base
HERE = dev.HERE
BOUND = HERE / "facilitator-bound-field-evidence/results.json"
LEGACY = HERE / "facilitator-source-relation-evidence/brief-replay.json"
TEST = HERE / "facilitator-event-transfer-evidence/results.json"
MODES = ("quote", "agreement")


def packet_id(panel, mask):
    return f"{panel}/{2 * int(0 in mask) + int(1 in mask)}"


def development():
    archived = dev.load(BOUND)["grades"]
    for packet, _, _, truth, mask, actions, reads in dev.fixtures():
        panel = packet.rsplit("/", 1)[0]
        assert packet == packet_id(panel, mask)
        expected = base.decision(truth, mask)
        for mode in MODES:
            action = actions[mode]
            row = archived[f"{packet}/{action}"]
            assert row["disposition"] == action and row["expected"] == expected
            yield panel, mode, mask, reads[mode], expected, action, row["strict"]
    old = dev.load(LEGACY)["panel_relations"]
    for entry, (truth, _, briefs) in zip(old, base.cases(), strict=True):
        family, number = entry["panel"]
        assert tuple(entry["variants"]["authored_relations"]) == truth
        for mode in MODES:
            reads = tuple(entry["variants"]["quote_only" if mode == "quote" else "agreement"])
            for index, brief in enumerate(briefs):
                mask = frozenset(i for i, bit in enumerate((index & 2, index & 1)) if bit)
                expected = base.decision(truth, mask)
                assert expected == brief["expected_disposition"]
                action = base.decision(reads, mask)
                usable = brief["arms"]["frozen_source_reader"]["strict"] and action == expected
                yield f"{family}-{number}", mode, mask, reads, expected, action, usable


def held_out():
    archive = dev.load(TEST)
    for packet, _, truth, mask, _, _ in transfer.packets():
        panel = packet.rsplit("/", 1)[0]
        expected = base.decision(truth, mask)
        for mode in MODES:
            reads = tuple(archive["readings"][f"{panel}/S{i}"][mode] for i in (1, 2))
            action = base.decision(reads, mask)
            row = archive["bound_grades"][f"{packet}/{action}"]
            assert row["disposition"] == action and row["expected"] == expected
            yield panel, mode, mask, reads, expected, action, row["strict"]


def collect(rows):
    cases = {}
    for panel, mode, mask, reads, expected, action, strict in rows:
        item = cases.setdefault((panel, mode), {"reads": reads, "receipts": {}})
        assert item["reads"] == reads
        assert mask not in item["receipts"]
        item["receipts"][mask] = {"expected": expected, "action": action, "strict": strict}
    assert all(len(row["receipts"]) == 4 for row in cases.values())
    return cases


def rewards(row):
    action, expected = row["action"], row["expected"]
    false = action != "withhold" and action != expected
    right = action != "withhold" and action == expected
    return int(right) - int(false), int(right and row["strict"]) - int(false)


def training_batch(cases):
    states, _, _, _ = base.trajectories()
    paths = defaultdict(float)
    for case in cases.values():
        reads, values = case["reads"], case["receipts"]
        for (left, right), mass in base.base.roster("training").items():
            start_left, _ = states["first", base.local(left, reads)]
            for left_slot, first in enumerate((*left, base.PASS)):
                for ok, ack, first_mass in base.events(first):
                    seen = base.observation(first, reads, ack)
                    start_right, _ = states["second", base.local(right, reads, seen)]
                    for right_slot, second in enumerate((*right, base.PASS)):
                        for second_ok, second_mass in ((True, base.base.CHAIR), (False, 1 - base.base.CHAIR)):
                            mask = base.delivered(first, ok, second, second_ok)
                            indices = (start_left + left_slot, start_right + right_slot)
                            key = (*indices, base.paid(first, second), *rewards(values[mask]))
                            paths[key] += mass * first_mass * second_mass / len(cases)
    actions = np.array([(a, b) for a, b, *_ in paths], dtype=int)
    payoffs = {name: np.array([(cost, 0.0, 35 + values[column], 0.0)
                              for _, _, cost, *values in paths]) for column, name in enumerate(("decision", "brief"))}
    return states, actions, payoffs, {"design_mixture": np.array(list(paths.values()))}


def evaluate(cases, policies, inventory):
    outcomes = {}
    for name, strategy, weights in policies:
        records = {}
        for (panel, mode), row in cases.items():
            # The distribution of actual receipts depends on the actor reads and link odds.
            # The truth argument is for the original helper's discarded decision metrics.
            stats, receipts = base.distribution(strategy, weights, base.base.roster(inventory), row["reads"], row["reads"])
            out = Counter(send_cost=stats["cost"])
            for label, mask in (
                ("none", frozenset()), ("slot_1_only", frozenset({0})),
                ("slot_2_only", frozenset({1})), ("both", base.TARGETS),
            ):
                out[f"receipt_{label}"] = receipts.get(mask, 0.0)
            for mask, probability in receipts.items():
                entry = row["receipts"][mask]
                action = entry["action"]
                decision, brief = rewards(entry)
                out["decision_payoff"] += probability * decision
                out["brief_payoff"] += probability * brief
                out["false_action"] += probability * (action != "withhold" and entry["expected"] != action)
                for label in ("retain", "revise", "withhold"):
                    out[f"usable_{label}"] += probability * (entry["strict"] and entry["expected"] == label)
            out["decision_net"] = out["decision_payoff"] - out["send_cost"]
            out["brief_net"] = out["brief_payoff"] - out["send_cost"]
            records[f"{panel}/{mode}"] = dict(out)
        summary = {}
        for mode in (*MODES, "mean"):
            selected = [v for k, v in records.items() if mode == "mean" or k.endswith("/" + mode)]
            summary[mode] = {k: sum(r[k] for r in selected) / len(selected) for k in selected[0]}
        outcomes[name] = {"summary": summary, "cases": records}
    return outcomes


def run():
    train = collect(development())
    assert len(train) == 20
    states, actions, outcomes, mass = training_batch(train)
    optimizer = base.base.optimizer
    trace = {}
    fitted = {}
    for name, payoff in outcomes.items():
        trace[name], fit = optimizer.fit(states, actions, payoff, mass)
        fitted[name] = base.base.observed_weights(states, fit["joint_learned"])
    frozen = dev.transfer.policy(dev.transfer.FROZEN)
    assert all(p.keys() == frozen.keys() for p in fitted.values())
    policies = [(name, "learned", weights) for name, weights in fitted.items()]
    policies += [(f"{name}_erased", "learned_erased", weights) for name, weights in fitted.items()]
    policies += [("frozen", "learned", frozen), ("frozen_erased", "learned_erased", frozen), ("greedy", "greedy", {})]
    practice = evaluate(train, policies, "training")
    for name in outcomes:
        assert abs(practice[name]["summary"]["mean"][f"{name}_net"] - trace[name][-1]["record_reward"]) < 1e-9
    test = collect(held_out())
    assert len(test) == 8 and not {p for p, _ in train} & {p for p, _ in test}
    results = {roster: evaluate(test, policies, roster) for roster in ("split", "overlap")}
    parent = dev.load(TEST)["replay"]
    for roster, rows in results.items():
        for mode in MODES:
            for name, variant in (("frozen", "learned"), ("frozen_erased", "erased"), ("greedy", "greedy")):
                assert abs(rows[name]["summary"][mode]["brief_net"] -
                           parent[roster][f"{mode}_{variant}"]["mean"]["net_actionable"]) < 1e-9
    dependencies = (Path(__file__), Path(base.__file__), Path(optimizer.__file__),
                    BOUND, LEGACY, TEST, base.CITATIONS, dev.transfer.FROZEN)
    return {"scope": "Two matched from-uniform joint exact-policy-gradient fits. Only the reward condition differs. "
                     "Fit uses 10 exposed development proposals and two frozen reader channels. Held-out dockets are "
                     "excluded from fitting and serve as a retrospective transfer test. No LLM weight updates.",
            "actor_states": len(states), "trajectory_rows": len(actions),
            "updates_per_fit": optimizer.STEPS, "trace": trace,
            "development_receipts_with_reward_difference": sum(
                rewards(row)[0] != rewards(row)[1] for case in train.values() for row in case["receipts"].values()),
            "training_cases": [{"panel": panel, "channel": mode, "local_reads": row["reads"],
                                "receipt_rewards": [{"seen": sorted(mask), "rewards": rewards(mark)}
                                                    for mask, mark in row["receipts"].items()]}
                               for (panel, mode), row in train.items()],
            "file_sha256": {str(p.resolve().relative_to(HERE.parents[1])): sha256(p.read_bytes()).hexdigest()
                            for p in dependencies},
            "train": practice, "transfer": results,
            "policies": {name: [{"state": k, "probabilities": v} for k, v in weights.items()] for name, weights in fitted.items()}}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
