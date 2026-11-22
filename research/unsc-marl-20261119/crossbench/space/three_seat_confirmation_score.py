"""Replay paid, authorized confirmation through the frozen disclosure policy."""
import argparse
from collections import defaultdict
from itertools import product
import json
from pathlib import Path
from unittest.mock import patch

import torch

import three_seat_confirmation as call
import three_seat_commitment_replay as prior

HERE = Path(__file__).resolve().parent
base = prior.base
shared = prior.shared
FEE = .08
ROUND_TRIP = .81


def read_receipts(raw):
    results, audited = {}, []
    for package, grade in call.language.VOCABULARY:
        intended = ("ABC".index(package), grade)
        for permitted in (True, False):
            prefix = "permitted" if permitted else "withheld"
            row = raw[f"{prefix}/{package}{grade}"]
            confirmation = row["output"] == f"CONFIRM {package} {grade}" and row["ended"]
            declined = row["output"] == "DECLINE" and row["ended"]
            valid = confirmation if permitted else declined
            results[intended, permitted] = confirmation
            audited.append({"tuple": intended, "permitted": permitted, "exact_reply": valid,
                            "confirmation": confirmation, "decline": declined, "text": row["output"]})
    return results, audited


def candidate_views(data, weights, unknown):
    grid = data.grid
    for world, weight in data.prior.items():
        a_state = data.states["A", world[0]]
        for (i, pay), a in zip(base.ACTIONS, weights[a_state, :len(base.ACTIONS)], strict=True):
            first = grid.claim(world, 0, i)
            admitted = None if first == unknown else first
            for peer, link in base.observations(admitted, pay):
                b_state = data.states["B", world[1], peer]
                for j, b in enumerate(weights[b_state, :3]):
                    second = grid.claim(world, 1, j)
                    for one, two in product((False, True), repeat=2):
                        original = (first if one else None, second if two else None)
                        verified = tuple(None if item == unknown else item for item in original)
                        chance = (base.DELIVER if one else 1 - base.DELIVER) * (
                            base.DELIVER if two else 1 - base.DELIVER)
                        yield weight * a * link * b * chance, pay, world, original, verified


def query_candidates(grid, original, verified, require_proof=True):
    for seat, claim in enumerate(original):
        if claim is None or verified[seat] is not None:
            continue
        promoted = tuple(claim if i == seat else old for i, old in enumerate(verified))
        if not require_proof or grid.information(promoted)[1]:
            yield seat, claim, promoted


def evaluate(grid, views, table, authority_probability, mode):
    totals = defaultdict(float)
    for p, pay, world, offered, verified in views:
        _, initial = grid.information(verified)
        totals["mass"] += p
        totals["before_confirmation"] += p * bool(initial)
        totals["peer_cost"] += p * base.FEE * pay
        if initial:
            totals["warranted"] += p
            continue
        question = next(query_candidates(grid, offered, verified, mode != "any_pending"), None)
        if question is None or mode == "drop":
            continue
        _, claim, promoted = question
        totals["question_rate"] += p
        _, outcomes = grid.information(promoted)
        assert outcomes <= grid.winners(world)
        confirmed = authority_probability * table[claim, True]
        unconfirmed = (1 - authority_probability) * table[claim, False]
        totals["withheld_confirmation_attempts_delivered"] += p * ROUND_TRIP * unconfirmed
        totals["warranted"] += p * ROUND_TRIP * confirmed * bool(outcomes)
        if mode == "trust_text":
            totals["unwarranted_certification"] += p * ROUND_TRIP * unconfirmed
    assert abs(totals.pop("mass") - 1.) < 1e-9
    points = dict(totals)
    # Use a common schema even in arms where no request is made.
    for key in ("warranted", "question_rate", "withheld_confirmation_attempts_delivered", "unwarranted_certification"):
        points.setdefault(key, 0.)
    points["warranted_net"] = points["warranted"] - FEE * points["question_rate"] - points["peer_cost"]
    return points


def example(grid, views):
    eligible = []
    for mass, _, _, offered, verified in views:
        if grid.information(verified)[1]:
            continue
        query = next(query_candidates(grid, offered, verified), None)
        if query is not None:
            eligible.append((mass, offered, verified, query))
    if not eligible:
        return None
    _, offered, verified, (seat, claim, verified_after) = max(eligible, key=lambda row: row[0])
    before_worlds, before = grid.information(verified)
    after_worlds, after = grid.information(verified_after)
    assert not before and after
    return {"offered": offered, "verified_before": verified, "compatible_worlds_before": before_worlds,
            "question": {"speaker": seat, "claim": claim},
            "on_decline_or_loss": "unresolved", "compatible_worlds_after_confirmation": after_worlds,
            "warranted_after_authorized_confirmation": sorted(after)}


def run(scripted=False):
    torch.set_num_threads(1)
    certified_control = {(("ABC".index(p), n), allowed): allowed
                         for p, n in call.language.VOCABULARY for allowed in (True, False)}
    table, checks = (certified_control, []) if scripted else read_receipts(call.replay(call.ROOT))
    fit = json.loads(prior.transport.FIT.read_text())
    entries = {row["draw"]: row for row in json.loads(prior.fitted.REGISTRY.read_text())["accepted"]}
    stress = json.loads(prior.judge.ROOT.joinpath("decision-replay.json").read_text())["cases"]
    saved = {(r["grid"], r["foil"]): r for r in stress}
    negatives = [r for r in json.loads(prior.LANGUAGE.read_text())["records"]
                 if r["group"] == "matched_author_controls" and r["gold"] == "reject"]
    weights = torch.as_tensor(fit["weights"], dtype=torch.float64)
    rows = []
    for result in fit["reserved"]:
        identifier = result["grid_id"]
        with patch.dict(shared.FIXTURES, {"target": prior.fitted.fixture(entries[identifier])}):
            data = prior.fitted.data_for(shared.Grid("target"))
            choices = data.probabilities(weights).numpy()
            for foil in negatives:
                changed = ("ABC".index(foil["p"]), foil["grade"])
                views = tuple(candidate_views(data, choices, changed))
                witness = example(data.grid, views)
                for rate in (0., .5, 1.):
                    variants = {name: evaluate(data.grid, views, answers, rate, mode)
                                for name, answers, mode in (
                                    ("drop_provisional", table, "drop"),
                                    ("model_verified_confirmation", table, "authorized"),
                                    ("model_text_only", table, "trust_text"),
                                    ("model_verify_any_pending", table, "any_pending"),
                                    ("scripted_confirmation", certified_control, "authorized"),
                                )}
                    previous = saved[identifier, foil["id"]]["reference_reject"]["warranted_net"]
                    assert abs(variants["drop_provisional"]["warranted_net"] - previous) < 1e-9
                    assert variants["model_verified_confirmation"]["unwarranted_certification"] == 0.
                    rows.append({"grid": identifier, "foil": foil["id"],
                                 "authority_probability": rate, "policies": variants, "case_witness": witness})
    means = {}
    for rate in (0., .5, 1.):
        group = [row["policies"] for row in rows if row["authority_probability"] == rate]
        means[str(rate)] = {name: {k: float(sum(row[name][k] for row in group) / len(group)) for k in scores}
                            for name, scores in group[0].items()}
    no_request = means["1.0"]["drop_provisional"]["warranted"]
    authority_full = means["1.0"]["model_verified_confirmation"]
    gain = authority_full["warranted"] - no_request
    break_even = FEE * authority_full["question_rate"] / gain if gain > 0 else None
    return {
        "scope": "Deliberate stress replay under synthetic private authority. Every substituted grade is "
                 "numerically correct yet provisional. A fixed chair asks only if the confirmation would "
                 "complete a proof. The simulator independently enforces speaker authority in the verified arm. "
                 "The policy and model are frozen, and rates are assumptions, not historical estimates.",
        "confirmation_fee": FEE, "round_trip": ROUND_TRIP,
        "model_replies": checks, "means_by_authority_probability": means,
        "break_even_authority_rate_for_fixed_query_rule": break_even, "cases": rows,
    }


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--scripted-reference", action="store_true",
                     help="Replay the deterministic authority-respecting responder without running a model.")
    args = cli.parse_args()
    result = run(args.scripted_reference)
    if args.scripted_reference:
        aliases = {"drop_provisional": "drop_provisional",
                   "scripted_confirmation": "scripted_confirmation",
                   "scripted_verify_any_pending": "model_verify_any_pending"}
        result = {"scope": "Deterministic scripted reference. The same authority-respecting reply is used "
                           "for selective and broad query policies. No model replies are scored.",
                  "results": {p: {mode: scores[alias] for mode, alias in aliases.items()}
                              for p, scores in result["means_by_authority_probability"].items()},
                  "break_even_authority_probability": result["break_even_authority_rate_for_fixed_query_rule"]}
    print(json.dumps(result, indent=2))
