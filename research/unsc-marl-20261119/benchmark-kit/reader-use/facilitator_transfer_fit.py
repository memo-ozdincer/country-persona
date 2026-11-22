"""Fit on archived facilitator briefs and replay on family-disjoint cohorts."""
from hashlib import sha256
import json
from pathlib import Path
from unittest.mock import patch

import facilitator_mixed_votes_score as mixed
import facilitator_new_meetings_score as recent
import facilitator_receipt_ceiling as ceiling
import facilitator_receipt_search as exact

HERE = ceiling.HERE
record = ceiling.prior.record
base = ceiling.base
MODE = "routing"
OLD_TEST = HERE / "facilitator-new-meetings-evidence/results.json"
MIXED_TEST = HERE / "facilitator-mixed-votes-evidence/results.json"


def mode_bank(bank, mode):
    return {(panel, MODE): case for (panel, source), case in bank.items()
            if source == mode}


def split():
    train = {}
    for bank in ceiling.datasets().values():
        for (panel, source), case in bank.items():
            key = (panel, MODE)
            assert key not in train and source == ceiling.MODE
            train[key] = case
    old = base.endpoint.delivery.load(OLD_TEST)
    existing = old["source_relations"]
    mask_rows = []
    for packet, _, _, _, seen, _ in recent.packets():
        panel, _ = packet.rsplit("/", 1)
        reads = tuple(existing[f"{panel}/S{i}"]["literal"] for i in (1, 2))
        grade = old["grades"][f"{packet}/literal"]
        mask_rows.append((panel, MODE, seen, reads, grade["expected"], grade["disposition"], grade["strict"]))
    prose = record.collect(mask_rows)
    archive = base.endpoint.delivery.load(MIXED_TEST)
    votes, receipts = mixed.receipts(archive["readings"])
    for key, value in receipts.items():
        saved = archive["receipts"][key]
        assert saved == json.loads(json.dumps(value))
    cohorts = {
        "guinea_libya": prose,
        "space_gaza_bound": mode_bank(votes, "combined_bound"),
        "space_gaza_roll_call": mode_bank(votes, "roll_call"),
    }
    assert len(train) == 12 and {k: len(v) for k, v in cohorts.items()} == {
        "guinea_libya": 6, "space_gaza_bound": 8, "space_gaza_roll_call": 8,
    }
    assert not set(train) & set().union(*(set(cohort) for cohort in cohorts.values()))
    return train, cohorts


def swap_bank(bank):
    return {(panel, mode): {"reads": tuple(reversed(row["reads"])),
                            "receipts": {frozenset(1 - i for i in mask): value for mask, value in row["receipts"].items()}}
            for (panel, mode), row in bank.items()}


def augmented(bank):
    mirrored = {(panel + "/swapped", mode): row for (panel, mode), row in swap_bank(bank).items()}
    return bank | mirrored


def fit(bank, acknowledge):
    optimizer = base.base.optimizer
    if acknowledge:
        states, actions, reward, mass = record.training_batch(bank)
    else:
        with patch.object(base, "observation", return_value=None):
            states, actions, reward, mass = record.training_batch(bank)
    trace, trained = optimizer.fit(states, actions, reward["brief"], mass)
    learn = base.base.observed_weights(states, trained["joint_learned"])
    init = base.base.observed_weights(states, trained["initial_uniform"])
    strategy = "learned" if acknowledge else "learned_erased"
    arms = [("initial", strategy, init), ("fitted", strategy, learn)]
    with patch.object(record, "MODES", (MODE,)):
        practice = record.evaluate(bank, arms, "training")
    for key, entry in (("initial", trace[0]), ("fitted", trace[-1])):
        assert abs(practice[key]["summary"][MODE]["brief_net"] - entry["record_reward"]) < 1e-9
    return learn, {"updates": optimizer.STEPS, "state_count": len(states), "trajectory_rows": len(actions),
                   "trace": trace, "practice": {k: r["summary"][MODE] for k, r in practice.items()}}


def evaluate(cohort, policies):
    observed = {}
    for layout in ("split", "overlap"):
        with patch.object(record, "MODES", (MODE,)):
            normal = record.evaluate(cohort, policies, layout)
            swapped = record.evaluate(swap_bank(cohort), policies, layout)
        bounds = {}
        for name, ack in (("adaptive", True), ("independent", False)):
            _, _, grid = ceiling.tensor(cohort, layout, ack)
            bounds[name] = exact.maximize(grid)
        assert bounds["adaptive"]["exact_net"] + 1e-9 >= max(
            r["summary"][MODE]["brief_net"] for r in normal.values())
        assert bounds["independent"]["exact_net"] + 1e-9 >= normal["trained_independent"]["summary"][MODE]["brief_net"]
        observed[layout] = {"systems": normal, "swapped_summaries": {k: r["summary"][MODE] for k, r in swapped.items()},
                            "bounds": bounds}
    return observed


def run():
    train, tests = split()
    bank = augmented(train)
    with_ack, learned = fit(bank, True)
    no_ack, independent = fit(bank, False)
    frozen, initial_independent = ceiling.stock()
    policies = (
        ("trained_adaptive", "learned", with_ack), ("trained_erased", "learned_erased", with_ack),
        ("trained_independent", "learned_erased", no_ack), ("frozen", "learned", frozen),
        ("old_independent", "learned_erased", initial_independent), ("greedy", "greedy", {}),
    )
    exact.check()
    results = {cohort: evaluate(cases, policies) for cohort, cases in tests.items()}
    reference = base.endpoint.delivery.load(OLD_TEST)["routing"]
    for layout in ("split", "overlap"):
        for name in ("frozen", "greedy"):
            assert results["guinea_libya"][layout]["systems"][name]["summary"][MODE] == reference[layout]["policies"][name]["summary"]["literal"]
    ref_mixed = base.endpoint.delivery.load(MIXED_TEST)["routing"]
    for cohort, mode in (("space_gaza_bound", "combined_bound"), ("space_gaza_roll_call", "roll_call")):
        for layout in ("split", "overlap"):
            for name in ("frozen", "greedy"):
                assert results[cohort][layout]["systems"][name]["summary"][MODE] == ref_mixed[layout]["policies"][name]["summary"][mode]
    files = (Path(__file__), Path(record.__file__), Path(ceiling.__file__), Path(base.base.optimizer.__file__),
             Path(exact.__file__), ceiling.EVIDENCE, ceiling.POLICIES, ceiling.prior.RESULTS, record.TEST,
             record.dev.EVIDENCE, record.dev.QUOTE, OLD_TEST, MIXED_TEST, Path(mixed.__file__))
    return {
        "scope": "Exact joint policy-gradient optimization for two decentralized desks. Train on archived brief grades "
                 "with both assignments of documentary positions. Two matched runs differ only in availability of "
                 "acknowledgment. Payoff rewards correct strict publishable briefs, penalizes false actions and "
                 "subtracts payload cost. Test meeting families are excluded from policy fitting. Test cohorts use "
                 "archived generated readers and compiled fields. Acknowledgment is free. Zero language model updates.",
        "train_panel_ids": [panel for panel, _ in train],
        "train_augmented_panel_ids": [panel for panel, _ in bank],
        "training_receipts": {
            panel: {"observed_relations": item["reads"],
                    "receipts": [{"seen": sorted(mask), **grade}
                                 for mask, grade in item["receipts"].items()]}
            for (panel, _), item in train.items()
        },
        "test_panel_ids": {k: [panel for panel, _ in v] for k, v in tests.items()},
        "fits": {"adaptive": learned, "independent": independent},
        "policy_tables": {k: [{"state": s, "action_probabilities": p} for s, p in v.items()]
                          for k, v in (("adaptive", with_ack), ("independent", no_ack))},
        "results": results,
        "sha256": {str(path.resolve().relative_to(HERE.parents[1])): sha256(path.read_bytes()).hexdigest() for path in files},
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
