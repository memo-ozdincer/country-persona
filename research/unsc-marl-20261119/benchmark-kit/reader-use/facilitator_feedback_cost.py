"""Compare feedback to a retrained independent router with the same brief writer."""
from collections import Counter
from hashlib import sha256
from itertools import product
import json
from pathlib import Path
from unittest.mock import patch

import facilitator_record_policy as record
import facilitator_witness_writer_score as writing

base = record.base
dev = record.dev
HERE = record.HERE
RESULTS = HERE / "facilitator-witness-writer-evidence/results.json"
FIELDS = HERE / "facilitator-witness-writer-evidence/transcript.jsonl"
TRANSFER_RUN = HERE / "facilitator-event-transfer-evidence/transcript.jsonl"


def fit_independent():
    relation_pairs = tuple(product(base.RELATIONS, repeat=2))
    categories = {status: base.decision(status, base.TARGETS) for status in relation_pairs}
    counts = Counter(categories.values())
    weights = {status: 1 / (len(counts) * counts[result]) for status, result in categories.items()}
    with patch.object(base, "observation", return_value=None):
        states, paths, rewards, masses = base.trajectories(weights)
    assert all(view[1] is None for role, view in states if role == "second")
    trace, fitted = base.base.optimizer.fit(states, paths, rewards, masses)
    learned = base.base.observed_weights(states, fitted["joint_learned"])
    value = sum(base.distribution("learned_erased", learned, base.base.roster("training"), status, status)[0]["net"]
                * prob for status, prob in weights.items())
    assert abs(value - trace[-1]["record_reward"]) < 1e-9
    return learned, trace


def cases():
    art = dev.load(RESULTS)
    transfer_readings = dev.load(record.TEST)["readings"]
    for scope, records in (("development", dev.fixtures()), ("transfer", writing.run.held.packets())):
        for row in records:
            if scope == "development":
                packet, _, truth, seen, reads = row[0], row[1], row[3], row[4], row[6]["quote"]
            else:
                packet, _, truth, seen, _, _ = row
                panel, _ = packet.rsplit("/", 1)
                reads = tuple(transfer_readings[f"{panel}/S{i}"]["quote"] for i in (1, 2))
            expected = base.decision(truth, seen)
            action = base.decision(reads, seen)
            mark = art["records"]["assertion"][f"{packet}/{action}"]["grade"]
            assert mark["expected"] == expected and mark["disposition"] == action
            yield scope, packet.rsplit("/", 1)[0], "quote", seen, reads, expected, action, mark["strict"]


def first_send_probability(strategy, weights, roster, reads):
    return sum(p * prob for (left, _), p in roster.items()
               for card, prob in base.choice(strategy, weights, "first", left, reads, base.PASS)
               if card is not None)


def compare(cases, policies, inventory):
    arms = [(name, strategy, weights) for name, strategy, weights, _ in policies]
    with patch.object(record, "MODES", ("quote",)):
        observed = record.evaluate(cases, arms, inventory)
    roster = base.base.roster(inventory)
    for name, strategy, weights, feedback in policies:
        rows = observed[name]["cases"]
        for (panel, mode), case in cases.items():
            row = rows[f"{panel}/{mode}"]
            row["payload_attempts"] = row["send_cost"] / base.FEE
            first = first_send_probability(strategy, weights, roster, case["reads"])
            row["ack_attempts"] = first * base.base.CHAIR if feedback else 0.0
            row["ack_deliveries"] = row["ack_attempts"] * base.base.PEER
        observed[name]["mean"] = {k: sum(row[k] for row in rows.values()) / len(rows)
                                  for k in ("brief_payoff", "brief_net", "usable_retain", "usable_revise",
                                            "false_action", "payload_attempts", "ack_attempts", "ack_deliveries")}
    return observed


def frontier(observed):
    learned = observed["learned"]["mean"]
    independent = observed["independent"]["mean"]
    greedy = observed["greedy"]["mean"]
    learned_savings = greedy["payload_attempts"] - learned["payload_attempts"]
    publish_gap = greedy["brief_payoff"] - learned["brief_payoff"]
    break_even = publish_gap / learned_savings if learned_savings > 0 else None
    ack_limit = (learned["brief_net"] - independent["brief_net"]) / learned["ack_attempts"]
    return {"learned_vs_greedy_payload_fee_at_free_ack": break_even,
            "learned_vs_independent_ack_fee_at_default_payload_fee": ack_limit,
            "net": [{"payload_fee": fee, "ack_fee": ack,
                     "values": {name: row["mean"]["brief_payoff"] - fee * row["mean"]["payload_attempts"]
                                - ack * row["mean"]["ack_attempts"] for name, row in observed.items()}}
                    for fee, ack in ((0., 0.), (base.FEE, 0.), (.15, 0.), (base.FEE, .05), (base.FEE, .10))]}


def shared_inference():
    totals = {}
    for name, path, suffix in (("transfer_field", FIELDS, "/assertion"),
                               ("transfer_witness", TRANSFER_RUN, "/witness")):
        rows = [row for row in map(json.loads, path.read_text().splitlines())
                if row["id"].startswith(("abyei-", "central-african-republic-")) and row["id"].endswith(suffix)]
        assert len(rows) == 8
        totals[name] = {"calls": len(rows), "input_tokens": sum(len(row["input_ids"]) for row in rows),
                        "output_tokens": sum(len(row["output_ids"]) for row in rows)}
    return totals


def run():
    independent, trace = fit_independent()
    frozen = dev.transfer.policy(dev.transfer.FROZEN)
    policies = (
        ("learned", "learned", frozen, True),
        ("learned_erased", "learned_erased", frozen, False),
        ("independent", "learned_erased", independent, False),
        ("greedy", "greedy", {}, True),
        ("greedy_independent", "greedy_erased", {}, False),
    )
    rows = list(cases())
    outcomes = {}
    for scope in ("development", "transfer"):
        tasks = record.collect(row[1:] for row in rows if row[0] == scope)
        assert len(tasks) == 4
        outcomes[scope] = {}
        for inventory in ("split", "overlap"):
            observed = compare(tasks, policies, inventory)
            outcomes[scope][inventory] = {"systems": observed, "price_sensitivity": frontier(observed)}
    parent = dev.load(RESULTS)["replay"]["transfer"]["assertion"]
    for inventory, trial in outcomes["transfer"].items():
        for name, old in (("learned", "quote_learned"), ("greedy", "quote_greedy"), ("learned_erased", "quote_erased")):
            got = trial["systems"][name]["mean"]["brief_net"]
            assert abs(got - parent[inventory][old]["mean"]["net_actionable"]) < 1e-9
    files = (Path(__file__), Path(base.__file__), Path(base.base.optimizer.__file__), RESULTS, FIELDS,
             TRANSFER_RUN, record.TEST, dev.transfer.FROZEN)
    return {"scope": "Independent routing retrained on the same synthetic balanced worlds as the frozen adaptive router. "
                     "All systems share the archived quote reads and speaker fields. Repricing holds policy weights fixed. "
                     "An acknowledgment is charged when a first payload arrived and its acknowledgment is attempted. "
                     "Shared inference represents the archived cache, not measured live cost.",
            "inference_cache": shared_inference(),
            "independent_updates": base.base.optimizer.STEPS, "independent_trace": trace,
            "independent_policy": [{"state": key, "probabilities": values} for key, values in independent.items()],
            "evaluations": outcomes,
            "file_sha256": {str(p.resolve().relative_to(HERE.parents[1])): sha256(p.read_bytes()).hexdigest() for p in files}}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
