"""Freeze and test scope verification on the Mali transfer family."""
import argparse
from collections import Counter
from itertools import product
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
SPACE = HERE.parent / "space"
sys.path.insert(0, str(SPACE))
import scope_sets
from scope_questions import SYSTEM as TIMING_SYSTEM, YES, NOT, exclude, load, runner
from scope_transfer import episode, Policy, POLICY

LOCK = HERE / "lock.json"
CASE = HERE / "case.json"
SCOPE = {"focused": "No independent monitoring in either reporting cycle.",
         "staged": "A binding commitment for independent monitoring in the second cycle only.",
         "broad": "Independent monitoring is operational in the first reporting cycle."}
CLAIMS = {
    "require_first": "Independent monitoring in the first reporting cycle is mandatory.",
    "forbid_first": "Independent monitoring in the first reporting cycle is forbidden.",
    "require_eventual": "Independent monitoring is mandatory in at least one of the two cycles.",
}
SETS = {
    "focused-or-staged": "Allow no independent monitoring or second-cycle-only monitoring. First-cycle monitoring is forbidden.",
    "staged-or-broad": "Allow second-cycle-only monitoring or first-cycle monitoring. Omitting monitoring entirely is forbidden.",
    "broad-only": "Require first-cycle monitoring. Omitting monitoring or only monitoring in the second cycle is forbidden.",
    "all": "Allow no monitoring, second-cycle-only monitoring or first-cycle monitoring.",
}
EXPECTED = {"france-overlap": {"focused"}, "france-impasse": {"focused", "staged"}, "russia": {"broad"}}
MENUS = {"france-overlap": {"A", "E", "G"}, "france-impasse": {"A", "G"}, "russia": {"C", "E"}}


def suite():
    case = load(CASE)
    for role, text in case["cards"].items():
        probes = [
            ("set", "scope", SETS,
             {"private_mandate": text},
             "Select the full set of monitoring timings allowed by the private mandate. Evaluate only when independent monitoring is required or forbidden. Ignore other fields. Output the answer letter."),
        ]
        probes.extend(("timing", key, {"true": YES, "false": NOT}, {"private_mandate": text, "claim": claim},
                       TIMING_SYSTEM) for key, claim in CLAIMS.items())
        for opt in case["options"]:
            description = " ".join((SCOPE[opt["scope"]],
                                     f"The extension is {opt['term']}. Aggregate reporting is {opt['report']}."))
            probes.append(("package", opt["id"], {"true": "The package meets every requirement.",
                                                 "false": "The package fails at least one requirement."},
                           {"private_mandate": text, "package": description},
                           "Apply all the mandate's requirements together. Choose the answer letter only."))
        for mode, item, choices, payload, prompt in probes:
            for order, ordered in enumerate((list(choices), list(reversed(choices)))):
                labels = "ABCD"[:len(choices)]
                args = {**payload, "answers": dict(zip(labels, (choices[k] for k in ordered), strict=True))}
                yield {"id": f"{role}/{mode}/{item}/{order}", "labels": labels, "values": ordered,
                       "messages": [{"role": "system", "content": prompt},
                                    {"role": "user", "content": json.dumps(args, ensure_ascii=False)}]}


def audited_menus(case):
    menus = {}
    for role in case["cards"]:
        menus[role] = {p["id"] for p in case["options"]
                       if p["scope"] not in EXPECTED[role] and
                       (p["term"] == "final" if role == "russia" else p["report"] == "public")}
    assert menus == MENUS
    return menus


def score(rows):
    case = load(CASE)
    menus = audited_menus(case)
    observed, scopes, result, counts = {}, {p: {} for p in ("timing", "whole_set", "tie", "authored")}, {}, Counter()
    plan = {item["id"]: item for item in suite()}

    def probes(base):
        winners, margins = [], []
        for order in range(2):
            key = f"{base}/{order}"
            values = plan[key]["values"]
            logits = dict(zip(values, rows[key]["label_logits"], strict=True))
            top = max(logits.values())
            choices = [k for k, v in logits.items() if v == top]
            winners.append(choices[0] if len(choices) == 1 else None)
            if "true" in logits:
                margins.append(logits["true"] - logits["false"])
        return winners[0] if winners[0] == winners[1] else None, margins, winners

    for role in case["cards"]:
        def truth_probe(kind, key):
            label, margins, orders = probes(f"{role}/{kind}/{key}")
            return {"sign": None if label is None else label == "true", "margins": margins, "orders": orders}

        observed[role] = {p["id"]: truth_probe("package", p["id"]) for p in case["options"]}
        timing = {key: truth_probe("timing", key) for key in CLAIMS}
        stable = {key: row["sign"] for key, row in timing.items()}
        whole, _, orders = probes(f"{role}/set/scope")
        margins = timing["require_first"]["margins"]
        rescue = min(margins) == 0 < max(margins) and whole == "broad-only" and stable["forbid_first"] is False
        scopes["timing"][role], _ = exclude(stable)
        scopes["whole_set"][role] = set(scope_sets.SCOPE_GROUPS[whole]) if whole else set()
        scopes["tie"][role], _ = exclude({**stable, "require_first": True} if rescue else stable)
        scopes["authored"][role] = EXPECTED[role]
        result[role] = {"timing": timing, "set": whole, "set_orders": orders, "tie_activated": rescue}
        for method, projection in scopes.items():
            counts[method, "exact_exclusion_set"] += projection[role] == EXPECTED[role]
    policy = Policy({tuple(obs): move for obs, move in load(POLICY)["policy"]})
    traces = {}
    for variant in ("france-overlap", "france-impasse"):
        cards = variant, "russia"
        target = "AGREEMENT_POSSIBLE" if variant.endswith("overlap") else "IMPASSE"
        truth = [menus[k] for k in cards]
        decisions = [observed[k] for k in cards]
        for opening in product(*(sorted(menu) for menu in truth)):
            for name, fields in scopes.items():
                for agent, strategy in (("strong", Policy()), ("learned", policy)):
                    route = episode(case, cards, opening, decisions, truth, fields, strategy)
                    key = variant, name, agent
                    counts[*key, "paths"] += 1
                    counts[*key, "correct"] += route["public"]["state"] == target
                    counts[*key, "slots"] += route["slots"]
                    counts[*key, "rejected"] += sum(event.get("admitted") is False for event in route["events"])
                    traces["/".join((*key, "".join(opening)))] = route
    return {"totals": {"/".join(k): v for k, v in counts.items()}, "package_predictions": observed,
            "scope_probes": result, "published_scope_candidates": {
                name: {k: sorted(v) for k, v in fields.items()} for name, fields in scopes.items()},
            "paths": traces}


def hashes():
    files = (Path(__file__), CASE, HERE / "references.json", POLICY, SPACE / "scope_transfer.py",
             SPACE / "scope_questions.py", SPACE / "scope_sets.py", SPACE / "scope_policy.py",
             SPACE / "scope_policy_refit.py", HERE.parent / "decision_ledger.py",
             scope_sets.ENTAILMENT / "field_panel.py")
    return {str(f.resolve().relative_to(HERE.parents[1])): runner.digest(f) for f in files}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("lock", "run", "replay"))
    parser.add_argument("output", type=Path, nargs="?")
    parser.add_argument("--model", type=Path)
    args = parser.parse_args()
    if args.mode == "lock":
        audited_menus(load(CASE))
        assert len(list(suite())) == 66
        with LOCK.open("x") as fh:
            json.dump({"hashes": hashes(), "calls": 66, "slots": 8,
                       "main": "Exact timing projections, fixed tie rescue from the space family, full scope set, authored scopes. All paired against the frozen strong and learned schedules."}, fh, indent=2)
            fh.write("\n")
        return
    assert load(LOCK)["hashes"] == hashes()
    if args.mode == "run":
        scope_sets.field_panel.suite, scope_sets.field_panel.score = suite, score
        scope_sets.field_panel.main(args.model, args.output)
        return
    data = args.output / "predictions.jsonl"
    assert load(args.output / "complete.json") == {"records": 66, "sha256": runner.digest(data)}
    rows = list(map(json.loads, data.read_text().splitlines()))
    for entry, stored in zip(suite(), rows, strict=True):
        assert all(stored[k] == v for k, v in entry.items())
    res = score({row["id"]: row for row in rows})
    assert json.loads(json.dumps(res)) == load(args.output / "metrics.json")
    print(json.dumps({"calls": len(rows), "paths": len(res["paths"]), "hashes": len(hashes())}, indent=2))


if __name__ == "__main__":
    main()
