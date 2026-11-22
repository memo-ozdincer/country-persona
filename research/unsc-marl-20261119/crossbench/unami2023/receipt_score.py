"""Replay fixed transport plans on exact-reviewed generated final records."""
from collections import defaultdict
import json
from itertools import product
from pathlib import Path
import re
import sys

import receipt_writer as writer

transfer = writer.transfer
relay = transfer.relay
HERE = Path(__file__).resolve().parent
EVIDENCE = HERE / "receipt-evidence"
CITATION = re.compile(r"\[([A-Z][A-Z_-]+)\]")


def bank(directory, reviews):
    rows = writer.replay(directory)
    forms = transfer.read(reviews)
    assert forms["final_records_sha256"] == writer.runner.digest(directory / "final-records.json")
    assert forms["records"].keys() == rows.keys()
    spec = transfer.named_sources()[0]["unami"]
    verified = transfer.record_bank(spec)
    ids, public_ids, requirements, public, _, cap = spec
    assert {source for deps in requirements.values() for source in deps} == set(ids) | public_ids
    public_criteria = {rule for rule, deps in requirements.items() if deps <= public_ids}
    records = {}
    for tag, keys, _ in writer.records():
        raw, annotation = rows[tag], forms["records"][tag]
        selected = frozenset(keys)
        text = raw["output"]
        met = set(annotation["met"])
        assert all(requirements[rule] <= selected and spans and all(span in text for span in spans)
                   for rule, spans in annotation["met"].items())
        assert all(issue["span"] in text and issue["reason"] for issue in annotation["material_errors"])
        guard = not annotation["material_errors"]
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        cited = [CITATION.findall(line) for line in lines]
        citations_clear = (all(len(hits) == 1 for hits in cited)
                           and sorted(hit for hits in cited for hit in hits) == sorted(selected))
        output_clear = len(text.split()) <= cap and len(f"{public} {text}".split()) <= 175 and raw["ended"]
        raw_score = 7 * len(met | public_criteria)
        facts = 7 * len(met)
        verified_facts = verified[selected]["record_points"] - 7 * len(public_criteria)
        assert facts <= verified_facts
        records[selected] = {"opaque_id": tag, "received": list(keys), "record": f"{public} {text}".strip(),
                             "supplement": text, "record_points": raw_score, "optional_points": facts,
                             "licensed_optional_points": verified_facts, "guard_clear": guard,
                             "citations_clear": citations_clear, "form_clear": output_clear and citations_clear,
                             "releasable": guard and output_clear and citations_clear,
                             "met": annotation["met"], "material_errors": annotation["material_errors"],
                             "output_tokens": len(raw["output_ids"]), "input_tokens": len(raw["input_ids"]),
                             "words": len(text.split())}
    return ids, records, verified


def add(output, terminal, weight, child, fee=0., attempt=0.):
    row = output.setdefault(terminal, [0., 0., 0.])
    row[0] += weight * child[0]
    row[1] += weight * (child[1] + child[0] * fee)
    row[2] += weight * (child[2] + child[0] * attempt)


def scripted_distribution(tree, belief, pending):
    action, children = tree
    if action is None:
        return {pending: (sum(belief.values()), 0., 0.)}
    fee, observations = relay.transitions(belief, pending, action)
    result = {}
    for receipt, posterior in observations.items():
        for terminal, row in scripted_distribution(children[receipt], posterior, pending - {receipt}).items():
            add(result, terminal, 1., row)
    mass = sum(belief.values())
    for row in result.values():
        row[1] += fee * row[0] / mass
        row[2] += row[0]
    return result


def planned_dist(target, anchor, ids, reference, adaptive):
    initial = frozenset(target) - {anchor}

    def terminal(pending):
        return reference[frozenset(ids[i] for i in target if i not in pending)]["record_points"]

    if adaptive:
        _, tree = relay.plan(relay.DESIGN, initial, 3, terminal)
    else:
        _, tree = max((relay.plan(relay.DESIGN, initial, 3, terminal, route)
                       for route in product(range(2), repeat=3)), key=lambda result: result[0])
    return scripted_distribution(tree, relay.DESIGN, initial)


def attached(policy, mappings, ids, target, anchor, canonical=False):
    pending = [i for i in target if i != anchor]
    incoming = (ids[anchor], *(ids[i] for i in pending))
    rows = mappings[incoming]["matched_training_views"]
    result = {}
    for old_anchor, old_a, old_b in rows:
        a, left, right = (relay.KEYS.index(key) for key in (old_anchor, old_a, old_b))
        origin = tuple(sorted((a, left, right)))
        lookup = dict(zip((left, right), pending, strict=True))
        for missing, row in transfer.outcomes(policy, origin, a, relay.DESIGN, canonical).items():
            add(result, frozenset(lookup[i] for i in missing), 1 / len(rows), row)
    return result


def metrics(target, anchor, ids, distribution, records, verified):
    out = defaultdict(float)
    portfolio = defaultdict(float)
    for pending, (mass, cost, attempts) in distribution.items():
        names = frozenset(ids[i] for i in target if i not in pending)
        text = records[names]
        out["record_points"] += mass * text["record_points"]
        out["release_points"] += mass * text["record_points"] * text["releasable"]
        out["guard_fail_probability"] += mass * (not text["guard_clear"])
        out["form_fail_probability"] += mass * (not text["form_clear"])
        out["release_probability"] += mass * text["releasable"]
        out["communication_cost"] += cost
        out["contact_attempts"] += attempts
        out["confirmed_scope_complete"] += mass * (not pending)
        out["writer_input_tokens"] += mass * text["input_tokens"]
        out["writer_output_tokens"] += mass * text["output_tokens"]
        out["licensed_record_points"] += mass * verified[names]["record_points"]
        portfolio[",".join(sorted(names))] += mass
    assert abs(sum(portfolio.values()) - 1.) < 1e-9
    return dict(out), dict(portfolio)


def run(directory, reviews):
    ids, generated, verified = bank(directory, reviews)
    transfer_results = transfer.read(transfer.HERE / "adaptive-transfer-results.json")["transfer"]["unami"]
    alignment = transfer.read(transfer.HERE / "adaptive-align-results.json")["families"]["unami"]
    fixed = tuple(max(transfer_results["alias_detail"], key=lambda row:
                      row["scores"]["fixed_canonical"]["net_gain_over_anchor"])["slots"])
    adaptive = tuple(max(transfer_results["alias_detail"], key=lambda row:
                         row["scores"]["adaptive_canonical"]["net_gain_over_anchor"])["slots"])
    fitted = transfer.read(transfer.FROZEN)
    policy = {transfer.immutable(row["local_state"]): row["probabilities"] for row in fitted["policy"]}
    mapped = {(r["anchor"], *r["other_cards"]): r for r in alignment["rows"]}
    catalogue = {
        "protected_only": (tuple(ids), lambda target, a: {frozenset(target) - {a}: (1., 0., 0.)}),
        "full_target_solo": (tuple(ids), lambda target, a: {frozenset(): (1., 0., 0.)}),
        "direct_frozen_registry_order": (tuple(ids), lambda target, a: transfer.outcomes(policy, target, a, relay.DESIGN)),
        "aligned_frozen": (tuple(ids), lambda target, a: attached(policy, mapped, tuple(ids), target, a)),
        "aligned_canonical_reply": (tuple(ids), lambda target, a: attached(policy, mapped, tuple(ids), target, a, True)),
        "best_fixed_authored": (fixed, lambda target, a: planned_dist(target, a, fixed, verified, False)),
        "best_adaptive_authored": (adaptive, lambda target, a: planned_dist(target, a, adaptive, verified, True)),
    }
    routes = {}
    for name, (names, distribution) in catalogue.items():
        cases = []
        for target, anchor in relay.SCENARIOS:
            score, portfolio = metrics(target, anchor, names, distribution(target, anchor), generated, verified)
            protected = generated[frozenset({names[anchor]})]["record_points"]
            score["net_gain_over_generated_anchor"] = score["record_points"] - protected - score["communication_cost"]
            expected = verified[frozenset({names[anchor]})]["record_points"]
            score["net_gain_over_verified_anchor"] = score["licensed_record_points"] - expected - score["communication_cost"]
            cases.append({"target": [names[i] for i in target], "anchor": names[anchor],
                          "metrics": score, "record_distribution": portfolio})
        routes[name] = {
            "average": {metric: sum(row["metrics"][metric] for row in cases) / len(cases) for metric in cases[0]["metrics"]},
            "cases": cases,
        }
    for label, expected in (("aligned_frozen", alignment["average"]["aligned_joint"]["net_gain_over_anchor"]),
                            ("best_fixed_authored", max(row["scores"]["fixed_canonical"]["net_gain_over_anchor"]
                                                        for row in transfer_results["alias_detail"])),
                            ("best_adaptive_authored", max(row["scores"]["adaptive_canonical"]["net_gain_over_anchor"]
                                                           for row in transfer_results["alias_detail"]))):
        assert abs(routes[label]["average"]["net_gain_over_verified_anchor"] - expected) < 1e-9
    return {"scope": "One frozen writer per receipt set on a previously exposed target docket. The public paragraph is authored. "
                     "No router was selected using the generated records. The reviews are same-assistant with exact spans.",
            "bank": {",".join(sorted(ids)): row for ids, row in generated.items()}, "routes": routes}


if __name__ == "__main__":
    if len(sys.argv) > 2:
        raise SystemExit("Use receipt_score.py [review_file]")
    review = Path(sys.argv[1]) if len(sys.argv) == 2 else HERE / "receipt-annotations.json"
    print(json.dumps(run(EVIDENCE, review), indent=2, ensure_ascii=False))
