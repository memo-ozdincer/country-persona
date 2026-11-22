"""Replay frozen specialist and script routes through the actual Colombia writer."""
from collections import defaultdict
from importlib.util import module_from_spec, spec_from_file_location
from itertools import product
import json
from pathlib import Path
import re

import receipt_chair as writer
import roster_shift as roster

HERE = Path(__file__).resolve().parent
review_spec = spec_from_file_location("colombia_review", HERE / "score.py")
review_module = module_from_spec(review_spec)
review_spec.loader.exec_module(review_module)
final_review = review_module.final_review
EVIDENCE = HERE / "receipt-evidence"
CITATION = re.compile(r"\[([A-Z0-9]+(?:, [A-Z0-9]+)*)\]")
relay = roster.relay

FIXTURE = {
    "strong_label_correct": roster.CONDITIONS["strong_specialist_B"],
    "strong_label_wrong": roster.CONDITIONS["mislabelled_specialist_B"],
}


def reviewed(directory=EVIDENCE):
    raw = writer.replay(directory)
    annotations = json.loads((HERE / "receipt-annotations.json").read_text())
    assert annotations["transcript_sha256"] == writer.runner.digest(directory / "transcript.jsonl")
    assert raw.keys() == annotations["records"].keys()
    case = json.loads(writer.CASE.read_text())
    ids, verified = writer.compile_bank()
    public = verified[frozenset()]["text"]
    generated = {}
    for key, row in raw.items():
        body = row["output"]
        selected = frozenset(row["evidence_ids"])
        review = annotations["records"][key]
        assert "procedure" not in review["met"]
        assert review["met"].keys() <= verified[selected]["proof"].keys()
        label = {"met": {"procedure": [public], **review["met"]}, "guard_issues": review["guard_issues"]}
        full = f"{public}\n\n{body}"
        result = final_review(case["rules"], {**row, "output": full}, label)
        cited = {tag for group in CITATION.findall(body) for tag in group.split(", ")}
        cite_clear = cited == selected
        approved = (result["complete"] and result["source_guard_clear"] and cite_clear
                    and result["word_count"] <= 185 and len(body.split()) <= 155)
        generated[selected] = {**result, "record": full, "body": body, "licensed_points": verified[selected]["record_points"],
                               "cited_ids": sorted(cited), "citation_ids_clear": cite_clear, "releasable": approved,
                               "writer_input_tokens": len(row["input_ids"]), "writer_output_tokens": len(row["output_ids"])}
    assert len(generated) == len(raw)
    return ids, verified, generated


def scripted_weights(tree, belief, pending):
    desk, branches = tree
    mass = sum(belief.values())
    if desk is None:
        return {pending: (mass, 0., 0.)}
    fee, observations = relay.transitions(belief, pending, desk)
    weights = defaultdict(lambda: [0., 0., 0.])
    for card, posterior in observations.items():
        for ending, (p, costs, contacts) in scripted_weights(branches[card], posterior, pending - {card}).items():
            row = weights[ending]
            row[0] += p
            row[1] += costs + fee * p / mass
            row[2] += contacts + p
    return weights


def script(target, anchor, ids, verified, prior, adaptive):
    pending = frozenset(target) - {anchor}
    a, b = sorted(pending)
    same = dict(enumerate(range(len(ids))))
    swap = {**same, a: b, b: a}
    alternatives = []
    for labels in (same, swap):
        aliased = {tuple(tuple(sorted(labels[i] for i in holding)) for holding in world): mass
                   for world, mass in prior.items()}
        def terminal(left):
            return verified[frozenset(ids[labels[i]] for i in target if i not in left)]["record_points"]
        if adaptive:
            score, tree = relay.plan(aliased, pending, 3, terminal)
        else:
            score, tree = max((relay.plan(aliased, pending, 3, terminal, order)
                               for order in product(range(2), repeat=3)), key=lambda item: item[0])
        dist = {frozenset(labels[i] for i in left): row for left, row in
                scripted_weights(tree, aliased, pending).items()}
        alternatives.append((score, dist))
    return max(alternatives, key=lambda row: row[0])[1]


def metrics(target, anchor, ids, dist, actual, verified):
    sums = defaultdict(float)
    start = frozenset({ids[anchor]})
    mix = {}
    for unresolved, (p, cost, contacts) in dist.items():
        held = frozenset(ids[i] for i in target if i not in unresolved)
        observed = actual[held]
        ideal = verified[held]["record_points"]
        sums["record_points"] += p * observed["points"]
        sums["released_record_points"] += p * observed["points"] * observed["releasable"]
        sums["release_probability"] += p * observed["releasable"]
        sums["guard_fail_probability"] += p * (not observed["source_guard_clear"])
        sums["complete_probability"] += p * observed["complete"]
        sums["licensed_record_points"] += p * ideal
        sums["writer_input_tokens"] += p * observed.get("writer_input_tokens", 0)
        sums["writer_output_tokens"] += p * observed.get("writer_output_tokens", 0)
        sums["cost"] += cost
        sums["contacts"] += contacts
        sums["complete_required_cards"] += p * (not unresolved)
        mix[",".join(sorted(held))] = p
    assert abs(sum(mix.values()) - 1) < 1e-9
    sums["net_gain_over_actual_anchor"] = sums["record_points"] - actual[start]["points"] - sums["cost"]
    sums["net_gain_over_verified_anchor"] = sums["licensed_record_points"] - verified[start]["record_points"] - sums["cost"]
    return {"metrics": dict(sums), "packet_probabilities": mix}


def run():
    ids, verified, actual = reviewed()
    fitted = roster.transfer.read(HERE / "specialist-fit-results.json")
    heads = roster.transfer.read(HERE / "specialist-script-results.json")["families"]["colombia"]["strong_specialist_B"]
    mapping = roster.transfer.read(HERE / "verified-transfer.json")["aligned"]["rows"]
    cases = {(r["anchor"], *r["other_cards"]): r for r in mapping}
    trained = {roster.transfer.immutable(row["local_state"]):row["probabilities"] for row in fitted["policy"]}
    old = roster.actor_policy()
    results = {}
    for scenario, (strength, expert, kind) in FIXTURE.items():
        rows = []
        for target, anchor in relay.SCENARIOS:
            missing = sorted(set(target) - {anchor})
            entry = cases[(ids[anchor], *(ids[i] for i in missing))]
            prior = roster.distribution(missing, strength, expert, kind)
            hint = 1 - expert if kind == "wrong_hint" else expert
            plans = {
                "old_frozen": roster.remap(old, prior, target, anchor, entry, (0, 1)),
                "specialist": roster.remap(trained, prior, target, anchor, entry, (hint, 1-hint)),
                "specialist_canonical_reply": roster.remap(trained, prior, target, anchor, entry, (hint, 1-hint), True),
                "fixed_script": script(target, anchor, ids, verified, prior, False),
                "adaptive_script": script(target, anchor, ids, verified, prior, True),
                "pooled_all_three": {frozenset(): (1., 0., 0.)},
            }
            rows.append({name: metrics(target, anchor, ids, dist, actual, verified)
                         for name, dist in plans.items()})
        mean = roster.transfer.mean([{name: row["metrics"] for name,row in item.items()} for item in rows])
        for label, expected in (("fixed_script", heads["stronger_scripts"]["known_prior_fixed"]),
                                ("adaptive_script", heads["stronger_scripts"]["known_prior_adaptive"])):
            assert abs(mean[label]["net_gain_over_verified_anchor"] - expected) < 1e-9
        hint_case = "mislabelled_specialist_B" if kind == "wrong_hint" else "strong_specialist_B"
        fit_read = fitted["transfer"]["colombia"][hint_case]["mean"]
        assert abs(mean["specialist"]["net_gain_over_verified_anchor"] - fit_read["trained_joint"]["net_gain_over_anchor"]) < 1e-9
        results[scenario] = {"mean": mean, "rows": rows}
    right, wrong = (results[name]["mean"] for name in FIXTURE)
    key = "net_gain_over_actual_anchor"
    best, bad = right["specialist"][key], wrong["specialist"][key]
    crossover = {name: (right[name][key] - bad) / (best - bad) for name in ("old_frozen", "fixed_script")} if best > bad else {}
    field_audit = {}
    rules = verified[frozenset(ids)]["proof"]
    for rule in rules:
        licensed = [packet for packet in actual if rule in verified[packet]["proof"]]
        kept = [packet for packet in licensed if rule in actual[packet]["evidence_spans"]]
        field_audit[rule] = {"licensed": len(licensed), "kept": len(kept),
                             "missing_from": [sorted(packet) for packet in licensed if packet not in kept]}
    return {"scope": "Policy choices precede writing. Source-local frozen Qwen bodies are shared across every route. "
                     "The roll call is authored. Provisional peer notes accompany the corresponding delivered role cards. "
                     "Scores indicate same-assistant exact-span review, not independent human adjudication.",
            "bank": {",".join(sorted(k)): value for k, value in actual.items()}, "routes": results,
            "licensed_field_retention": field_audit, "break_even_hint_accuracy_on_actual_points": crossover}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, ensure_ascii=False))
