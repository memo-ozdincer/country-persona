"""Replay Qwen action choices through the evidence transport and writer."""
import argparse
from collections import Counter
from hashlib import sha256
from itertools import product
import json
from pathlib import Path

import numpy as np

from duplicate_card_buffered_fit import optimize
from duplicate_card_language import CASES, POLICY, inputs, scorer
from duplicate_card_outcome_policy import PRIORS, PRIVATE, RECEIPT, archived_profiles
from duplicate_card_transport import FAULTS, MASKS, mask_weight, simulate
from source_route_fit import MESSAGE_COST
from source_route_search import LEGAL, SIGNAL_COST


def options(phase, inventory):
    if phase == "signal":
        return (True, bool(inventory & 2))
    return LEGAL[inventory]


def from_logits(row, allowed, mode):
    scores = np.asarray(row["scores"], dtype=float)
    if mode == "legal_greedy":
        result = np.zeros(len(scores))
        result[np.argmax(np.where(allowed, scores, -np.inf))] = 1.
    elif mode == "greedy_with_pass":
        result = np.zeros(len(scores))
        key = int(scores.argmax())
        result[key if allowed[key] else 0] = 1.
    else:
        weights = np.exp(scores - scores.max())
        logits = weights / weights.sum() * row["legal_mass"]
        result = np.where(allowed, logits, 0.)
        result[0] += 1 - result.sum()
    return result


def evaluate_choices(rows, case, reference):
    result = {name: Counter() for name in ("signal", "delivery")}
    mismatches = []
    for obs, row in rows.items():
        name, phase, seat, inventory, own, peer = obs
        if name != case:
            continue
        real = reference[seat, inventory, 0 if phase == "signal" else 1 + 2 * own + peer]
        avail = options(phase, inventory)
        unrestricted = np.argmax(row["scores"])
        masked = np.argmax(np.where(avail, row["scores"], -np.inf))
        result[phase].update({"observations": 1, "greedy_matches": int(real == unrestricted),
                              "greedy_unsupported": int(not avail[unrestricted]),
                              "masked_matches": int(real == masked)})
        if real != unrestricted or real != masked:
            mismatches.append({"observation": obs, "reference": int(real), "unrestricted": int(unrestricted),
                               "legal_only": int(masked), "unsupported": bool(not avail[unrestricted])})
    return {"counts": result, "mismatches": mismatches}


def independent_rollout(rows, case, prior, values, rates, mode, reference):
    signal_fail, card_fail = rates
    distributions = {}
    for key, row in rows.items():
        if key[0] != case:
            continue
        _, phase, seat, inv, own, peer = key
        if mode == f"typed_{phase}":
            distribution = np.zeros(len(row["scores"]))
            action = reference[seat, inv, 0 if phase == "signal" else 1 + 2 * own + peer]
            distribution[action] = 1.
        else:
            decoder = "legal_greedy" if mode.startswith("typed_") else mode
            distribution = from_logits(row, options(phase, inv), decoder)
        distributions[key] = distribution
    receipts = np.zeros(4)
    counts = np.zeros(2)
    for inventory, world_weight in zip(PRIVATE, prior, strict=True):
        for bits in MASKS:
            signal_prob = float(np.prod([distributions[case, "signal", seat, inv, 0, 0][bits[seat]]
                                         for seat, inv in enumerate(inventory)]))
            if not signal_prob:
                continue
            mass = world_weight * signal_prob
            counts[0] += mass * sum(bits)
            for link in MASKS:
                signal_weight = mass * mask_weight(link, signal_fail)
                if not signal_weight:
                    continue
                action_probs = [distributions[case, "delivery", seat, inv, bits[seat], link[seat] * bits[1-seat]]
                                for seat, inv in enumerate(inventory)]
                for attempted in product(range(3), repeat=2):
                    delivery_weight = signal_weight * action_probs[0][attempted[0]] * action_probs[1][attempted[1]]
                    if not delivery_weight:
                        continue
                    counts[1] += delivery_weight * sum(bool(x) for x in attempted)
                    for keep in MASKS:
                        receipt = RECEIPT[attempted[0] * keep[0], attempted[1] * keep[1]]
                        receipts[receipt] += delivery_weight * mask_weight(keep, card_fail)
    assert np.isclose(receipts.sum(), 1.)
    observed = np.array([values[0, 0], values[0, 1], values[0, 2], values[1, 2]])
    cost = counts @ [SIGNAL_COST, MESSAGE_COST]
    buffer = np.array([receipts[:3].sum(), 0, 0, receipts[3]])
    return {
        "attempted_signals": counts[0], "attempted_deliveries": counts[1],
        "received_both_probability": receipts[3],
        "direct_net": float(receipts @ observed - cost),
        "buffered_net": float(buffer @ observed - cost),
        "direct_rejected_probability": float(receipts @ (observed == 0)),
        "buffered_rejected_probability": float(buffer @ (observed == 0)),
    }


def report(directory):
    from transformers import AutoTokenizer

    with inputs():
        rows = scorer.read(directory)
    launch = json.loads((directory / "launch.json").read_text())
    tokenizer = AutoTokenizer.from_pretrained(launch["model_path"], local_files_only=True)
    for row in rows.values():
        rendered = tokenizer.apply_chat_template(row["messages"], tokenize=False, add_generation_prompt=True,
                                                 enable_thinking=False)
        prefix = tokenizer.encode(rendered, add_special_tokens=False)
        assert prefix == row["input_ids"]
        for letter, token in zip(scorer.LETTERS[:len(row["legal"])], row["label_ids"], strict=True):
            assert tokenizer.encode(rendered + letter, add_special_tokens=False) == [*prefix, token]
        assert len(row["scores"]) == len(row["legal"]) and np.all(np.isfinite(row["scores"]))
        assert 0 <= row["legal_mass"] <= 1.
    table = np.array(json.loads(POLICY.read_text())["trained_tables"]["matched"])
    values, score_hashes = archived_profiles()
    archived = {"venezuela": values["venezuela_original_release"], "dprk": values["dprk_reordered_hybrid"]}
    report = {}
    for case in CASES:
        observed = [r for r in rows.values() if r["observation"][0] == case]
        data = {
            "correctness": evaluate_choices(rows, case, table),
            "mean_menu_probability": sum(r["legal_mass"] for r in observed) / len(observed),
            "min_menu_probability": min(r["legal_mass"] for r in observed),
            "input_tokens_over_observations": sum(len(r["input_ids"]) for r in observed),
            "evaluation": {},
        }
        value = archived[case]
        for name, prior in PRIORS.items():
            data["evaluation"][name] = {}
            for condition in ("none", "both_10", "both_25"):
                rates = FAULTS[condition]
                silent, _ = optimize(prior, value[1, 2] - value[0, 0], rates)["silent"]
                test = {mode: independent_rollout(rows, case, prior, value, rates, mode, table)
                        for mode in ("greedy_with_pass", "legal_greedy", "stochastic_with_pass",
                                     "typed_signal", "typed_delivery")}
                data["evaluation"][name][condition] = {
                    **test, "exact_buffered_silent": float(value[0, 0] + silent),
                    "typed_learned_policy": simulate(table, prior, value, *rates),
                }
        report[case] = data
    path = directory / "actions.jsonl"
    return {"observations": len(rows), "transcript_sha256": sha256(path.read_bytes()).hexdigest(),
            "score_hashes": score_hashes, "results": report,
            "scope": "Frozen next-token action readout and exact conditional replay. The language-model desks "
                     "receive the prose version of the fitted policy. Record scores come from archived outputs."}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    print(json.dumps(report(args.directory), indent=2))
