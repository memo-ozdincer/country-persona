"""Compare matched receipt-policy fits with and without credit for supported withholds."""
from hashlib import sha256
import json
from pathlib import Path
from unittest.mock import patch

import facilitator_attribution_extracts_route as extracts
import facilitator_claim_type_fit as archive
import facilitator_quote_order_score as quote

transfer = archive.prior
record = transfer.record
ceiling = transfer.ceiling
BASE = transfer.base
MODE = transfer.MODE
EXTRACTS = transfer.HERE / "facilitator-attribution-extracts-evidence/results.json"


def reference_relations():
    truth = quote.targets()
    for row in record.dev.fixtures():
        truth[row[0].rsplit("/", 1)[0]] = row[3]
    for packet, _, relations, *_ in record.transfer.packets():
        truth[packet.rsplit("/", 1)[0]] = relations
    for panel, _, _, relations, _ in transfer.recent.study.panels():
        truth[panel] = relations
    for entry in record.dev.load(record.LEGACY)["panel_relations"]:
        family, number = entry["panel"]
        truth[f"{family}-{number}"] = tuple(entry["variants"]["authored_relations"])
    votes = record.dev.load(transfer.MIXED_TEST)["receipts"]
    for key, grade in votes.items():
        if key.endswith("/combined_bound/3"):
            panel = key.removesuffix("/combined_bound/3")
            truth[panel] = tuple(transfer.mixed.relation(vote, grade["claimed_vote"])
                                 for vote in grade["recorded"])
    return truth


def full_scope(bank, truth):
    """Conservatively require every established side in legacy receipt-local grades."""
    rows = []
    for (panel, mode), row in bank.items():
        relations = truth[panel]
        expected = BASE.decision(relations, BASE.TARGETS)
        required = {i for i, relation in enumerate(relations) if relation != "unknown"}
        for mask, grade in row["receipts"].items():
            assert grade["expected"] == BASE.decision(relations, mask)
            strict = grade["strict"] and required <= mask and grade["action"] == expected
            rows.append((panel, mode, mask, row["reads"], expected, grade["action"], strict))
    return record.collect(rows)


def summarize_bank(bank):
    return {
        panel: {
            "reads": row["reads"],
            "masks": {str(2 * int(0 in mask) + int(1 in mask)): grade
                      for mask, grade in row["receipts"].items()},
        }
        for (panel, _), row in bank.items()
    }


def measure(bank, policies, layout, rewards):
    with patch.object(record, "MODES", (MODE,)):
        replay = record.evaluate(bank, policies, layout)
    means = {}
    for name, row in replay.items():
        mean = row["summary"][MODE]
        means[name] = {**mean, "full_record_net": mean["brief_net"] + mean["usable_withhold"]}
    bounds = {}
    for name, reward in rewards.items():
        with patch.object(record, "rewards", reward):
            bounds[name] = {
                strategy: transfer.exact.maximize(ceiling.tensor(bank, layout, ack)[2])["exact_net"]
                for strategy, ack in (("adaptive", True), ("independent", False))
            }
    for metric, reward in (("brief_net", "publication"), ("full_record_net", "full_record")):
        assert max(mean[metric] for mean in means.values()) <= bounds[reward]["adaptive"] + 1e-9
    return {"means": means, "ceilings": bounds, "cases": {k: v["cases"] for k, v in replay.items()}}


def run():
    raw, controls, _ = archive.datasets()
    raw = {key: row for key, row in raw.items() if not key[0].startswith("central-african-republic-")}
    truth = reference_relations()
    train = full_scope(raw, truth)
    informative = sorted(panel for (panel, _), row in train.items()
                         if any(mask and grade["strict"] and grade["expected"] == "withhold"
                                for mask, grade in row["receipts"].items()))
    assert informative == ["afghanistan-1", "unifil-3"]
    primary, _ = extracts.receipt_bank(json.loads(EXTRACTS.read_text()))
    tests = {"source_extracted": primary}
    for name in ("guinea_libya_exposed", "haiti_mali"):
        tests[name] = transfer.augmented(full_scope(controls[name], truth))
    assert not train.keys() & set().union(*(test.keys() for test in tests.values()))
    augmented = transfer.augmented(train)
    rewards = {"publication": record.rewards, "full_record": extracts.full_record_reward}
    frozen, independent = ceiling.stock()
    policies = [("frozen", "learned", frozen), ("archived_independent", "learned_erased", independent),
                ("greedy", "greedy", {})]
    fits = {}
    for name, reward in rewards.items():
        with patch.object(record, "rewards", reward):
            weights, fit = transfer.fit(augmented, acknowledge=True)
        fits[name] = {**fit, "weights": [{"state": state, "probabilities": odds}
                                       for state, odds in weights.items()]}
        policies.append((f"fit_{name}", "learned", weights))
    return {
        "scope": "Exact policy-gradient fits from the same uniform start on archived grades. Legacy strict grades "
                 "are restricted to the complete-reference disposition and all established sides. The primary "
                 "source-extract cases use the separately graded exact full-record receipt masks. Event families "
                 "were exposed in prior project work. No new language-model generations.",
        "fitting_receipts": summarize_bank(train), "informative_withhold_panels": informative,
        "fits": fits,
        "tests": {name: {layout: measure(bank, policies, layout, rewards)
                         for layout in ("split", "overlap")} for name, bank in tests.items()},
        "sha256": {str(path.relative_to(transfer.HERE)): sha256(path.read_bytes()).hexdigest()
                   for path in (Path(__file__), EXTRACTS, transfer.OLD_TEST, transfer.MIXED_TEST,
                                ceiling.EVIDENCE, ceiling.prior.RESULTS, record.LEGACY)},
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, ensure_ascii=False))
