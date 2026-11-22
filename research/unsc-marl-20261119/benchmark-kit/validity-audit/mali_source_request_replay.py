"""Replay learned requests and exact independent dispatch under the observed prose reader."""
import argparse
from itertools import product
import json
from pathlib import Path

import numpy as np

from mali_source_request_reader import report as readings_report
from source_request_cases import hashes as case_hashes
from source_record_run import digest
import source_request_policy
from source_request_policy import (
    ACTIONS, BITS, DELIVERY_COST, JOINT, SEND, SIGNAL_COST, STATES, TEST_PRIORS, cases, evaluate, points,
    scripted,
)

STYLES = (("full", "missing"), ("reordered", "reversed"))


def shelf(decisions, style, reader):
    # The control matcher assumes a slot is valid based on its origin alone.
    views = np.zeros(8, dtype=int)
    truth_at_action = np.zeros((8, 4), dtype=int)
    for inventory in STATES:
        for field in range(1, 4):
            actual = field if inventory & BITS[field] else 0
            variant = style[0] if actual else style[1]
            reading = decisions[field, variant]
            assert reading["truth"] == actual
            proposed = actual if reader == "typed" else field if reader == "source_label" else reading["agreed_role"]
            if proposed and not (views[inventory] & BITS[proposed]):
                views[inventory] |= BITS[proposed]
                truth_at_action[inventory, proposed] = BITS[proposed] if proposed == actual else 0
    return views, truth_at_action


def weighted_matrix(prior, views, truth, payoffs, loss):
    held_out = np.zeros((8, 8, 4, 4))
    fees = DELIVERY_COST * np.add.outer((ACTIONS != 0).astype(int), ACTIONS != 0)
    for l, r in product(STATES, repeat=2):
        reward = -fees.copy()
        for keep_l, keep_r in product((0, 1), repeat=2):
            mass = (1 - loss if keep_l else loss) * (1 - loss if keep_r else loss)
            delivered = np.bitwise_or.outer(truth[l] * keep_l, truth[r] * keep_r)
            reward += mass * payoffs[delivered]
        held_out[views[l], views[r]] += prior[l, r] * reward
    return held_out


def best_silent(matrix):
    tables = np.asarray(list(product(*(np.flatnonzero(row) for row in SEND))))
    reply = np.zeros((len(tables), 8, 4))
    for left in STATES:
        for right in STATES:
            reply[:, right] += matrix[left, right, tables[:, left], :]
    reply = np.where(SEND[None], reply, -np.inf)
    winner = reply.max(axis=-1).sum(axis=1).argmax()
    return np.zeros(8, dtype=int), tables[winner], np.repeat(reply[winner].argmax(axis=-1)[:, None], 4, axis=1)


def run_policy(policy, prior, views, truth, payoff, loss, block_queries=False):
    ask, send, answer = policy
    assert np.all(JOINT[STATES, ask, send]) and np.all(SEND[STATES[:, None], answer])
    receipt = np.zeros(8)
    charges = invalid = 0.
    for l, r in product(STATES, repeat=2):
        q, a = ask[views[l]], send[views[l]]
        charges += prior[l, r] * SIGNAL_COST * (q != 0)
        for arrived, keep_l, keep_r in product((0, 1), repeat=3):
            p = prior[l, r] * np.prod([1 - loss if k else loss for k in (arrived, keep_l, keep_r)])
            b = answer[views[r], q if arrived and not block_queries else 0]
            bad = (a != 0 and truth[l, a] == 0) or (b != 0 and truth[r, b] == 0)
            invalid += p * bad
            charges += p * DELIVERY_COST * (int(a != 0) + int(b != 0))
            receipt[truth[l, a] * keep_l | truth[r, b] * keep_r] += p
    raw = receipt @ payoff
    assert np.isclose(receipt.sum(), 1)
    return {"proof_points": float(raw), "net": float(raw - charges),
            "unsupported_attempt_probability": float(invalid), "receipts": receipt.tolist()}


def source_witness(policy, views, truth, family):
    q, a, b = policy
    values = points(family)
    for left, right in product(STATES, repeat=2):
        ask, direct = q[views[left]], a[views[left]]
        answer, erased = b[views[right], ask], b[views[right], 0]
        delivered = truth[left, direct] | truth[right, answer]
        no_question = truth[left, direct] | truth[right, erased]
        if ask and values[delivered] > values[no_question]:
            return {"actual_inventories": [int(left), int(right)],
                    "request": family["fields"][ask - 1]["name"],
                    "response_changed_from": int(erased), "response_changed_to": int(answer),
                    "points": int(values[delivered]), "points_if_question_erased": int(values[no_question]),
                    "verified_record_addendum": [f for i, f in enumerate(family["fields"]) if delivered & (1 << i)]}
    return None


def report(reader_dir, policy_path):
    archive = json.loads(policy_path.read_text())
    policy_code = Path(source_request_policy.__file__)
    assert archive["source_hashes"] == {**case_hashes(), policy_code.name: digest(policy_code)}
    assert archive["fields"] == json.loads(json.dumps(cases()))
    learned = tuple(np.asarray(archive["training"][k]) for k in ("request", "left_delivery", "reply"))
    prior_prose = readings_report(reader_dir)
    decisions = {(r["field"], r["variant"]): r for r in prior_prose["readings"]}
    family = cases()["mali"]
    payoff = points(family)
    results, witnesses = [], []
    for style, reader in product(STYLES, ("typed", "source_label", "frozen_model")):
        views, truth = shelf(decisions, style, reader)
        if reader == "typed":
            assert np.array_equal(views, STATES)
        evidence = source_witness(learned, views, truth, family)
        witnesses.append({"style": style, "reader": reader, "example_if_links_hold": evidence})
        for label, prior in TEST_PRIORS.items():
            loss = .10
            matrix = weighted_matrix(prior, views, truth, payoff, loss)
            silent = best_silent(matrix)
            arms = {k: run_policy(p, prior, views, truth, payoff, loss)
                    for k, p in (("learned", learned), ("scripted", scripted()), ("exact_silent", silent))}
            arms["learned_question_erased"] = run_policy(learned, prior, views, truth, payoff, loss, block_queries=True)
            _, a, b = silent
            assert np.isclose(matrix[STATES[:, None], STATES[None, :], a[:, None], b[None, :, 0]].sum(),
                              arms["exact_silent"]["net"])
            if reader == "typed":
                assert np.isclose(arms["learned"]["net"], evaluate(learned, prior, payoff, loss)["net"])
                reference = next(r for r in archive["held_out"]["conditions"] if r["prior"] == label and r["loss"] == loss)
                assert np.isclose(arms["exact_silent"]["net"], reference["arms"]["optimal_independent"]["net"])
            results.append({"style": style, "reader": reader, "prior": label, "observed_masks": views.tolist(),
                            "arms": arms})
    return {"scope": "Mali is held out from three-field policy learning. Reading results come from frozen Qwen on "
                     "actual source-backed prose and controlled edits. An exact reference gate rejects unsupported "
                     "choices in the replay. Records are proof addenda created directly from delivered sources.",
            "policy_sha256": digest(policy_path), "reader": prior_prose, "rollouts": results, "witnesses": witnesses}


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("reader_directory", type=Path)
    cli.add_argument("policy", type=Path)
    args = cli.parse_args()
    print(json.dumps(report(args.reader_directory, args.policy), ensure_ascii=False, indent=2))
