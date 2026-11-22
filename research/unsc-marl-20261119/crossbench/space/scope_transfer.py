"""Transfer the frozen learned and scripted scope routers using visible, audited claims."""
import argparse
from collections import Counter
from hashlib import sha256
from itertools import product
import json
from pathlib import Path
import sys

import scope_policy as routing
from scope_policy_refit import Policy

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from decision_ledger import readout, truthful_disclosure

INITIAL = HERE / "evidence/metrics.json"
POLICY = HERE / "evidence/scope-policy-strong/results.json"
CASE = HERE / "case.json"


def read(path):
    return json.loads(path.read_text())


def episode(case, cards, opening, decisions, truth, scopes, strategy):
    roles = case["roles"]
    labels = [item["id"] for item in case["options"]]
    width = len(labels)

    def package_mask(names):
        return sum(1 << labels.index(name) for name in names)

    def names(bits):
        return [label for i, label in enumerate(labels) if bits & (1 << i)]

    known = [
        (package_mask(label for label, prediction in data.items() if prediction["sign"] is True),
         package_mask(label for label, prediction in data.items() if prediction["sign"] is False))
        for data in decisions
    ]
    events, claims = [], []
    public = (0, 0, 0, 0)

    def publish(role, bitmask, acceptance, step, action):
        nonlocal public
        claim = {"id": f"claim-{len(claims)+1}", "role": roles[role],
                 "accepts": names(bitmask) if acceptance else [],
                 "excludes": names(bitmask) if not acceptance else []}
        valid = truthful_disclosure(claim, truth[role])
        events.append({"slot": step, "type": action, "claim": claim, "admitted": valid})
        if valid:
            claims.append(claim)
            public = routing.record(public, role, bitmask, acceptance)
        return valid

    for role, package in enumerate(opening):
        mask = package_mask([package])
        if known[role][0] & mask:
            publish(role, mask, True, role - 2, "opening")
        else:
            events.append({"slot": role - 2, "type": "withheld_opening", "role": roles[role], "package": package})
    full = (1 << width) - 1
    step, role, available = 0, 1, 3
    while step <= width and not routing.terminal(public, full):
        obs, legal, baseline, ordinary = routing.move_options(width, public, known, role, step, available)
        if legal and strategy.get(obs, baseline):
            field = scopes[cards[role]]
            mask = package_mask(item["id"] for item in case["options"] if item["scope"] in field)
            events.append({"slot": step, "type": "check_scope", "role": roles[role], "scopes": sorted(field)})
            step += 1
            if mask:
                publish(role, mask, False, step, "scope")
            else:
                events.append({"slot": step, "type": "unreturned", "role": roles[role]})
            available &= ~(1 << role)
            role = 1 - role
        elif ordinary[0]:
            mask, _, next_role = ordinary
            yes, no = known[role]
            valid = publish(role, mask, bool(yes & mask), step, "package")
            if valid:
                role = next_role
            else:
                known[role] = yes & ~mask, no & ~mask
                role = 1 - role
        else:
            events.append({"slot": step, "type": "pass", "role": roles[role]})
            role = 1 - role
        step += 1
    outcome = readout(labels, roles, claims)
    assert routing.terminal(public, full) == (outcome["state"] in ("AGREEMENT_POSSIBLE", "IMPASSE"))
    return {"events": events, "public": outcome, "slots": step}


def assess(question_outputs):
    case = read(CASE)
    initial = read(INITIAL)
    fit = {tuple(obs): action for obs, action in read(POLICY)["policy"]}
    panel = read(question_outputs)["projections"]
    wording_panels = sorted(key.split("/")[0] for key in panel if key.endswith("/japan"))
    providers = {
        "authored": {"japan": {"broad"}, "china-overlap": {"focused"}, "china-impasse": {"focused", "staged"}},
        **{name: {card: set(panel[f"{name}/{card}"]["rejected_scopes"]) for card in case["cards"]}
           for name in wording_panels},
    }
    counts, paths = Counter(), {}
    labels = [item["id"] for item in case["options"]]
    for variant in ("china-overlap", "china-impasse"):
        cards = ("japan", variant)
        local = [{label: initial["decisions"][f"{card}/{label}"] for label in labels} for card in cards]
        truth = [[label for label, pred in items.items() if pred["expected"]] for items in local]
        target = "AGREEMENT_POSSIBLE" if variant == "china-overlap" else "IMPASSE"
        for opening in product(*truth):
            for provider, scopes in providers.items():
                for arm, strategy in (("strong", Policy()), ("learned", Policy(fit))):
                    trace = episode(case, cards, opening, local, truth, scopes, strategy)
                    key = variant, provider, arm
                    counts[*key, "paths"] += 1
                    counts[*key, "correct"] += trace["public"]["state"] == target
                    counts[*key, "slots"] += trace["slots"]
                    counts[*key, "checks"] += sum(e["type"] == "check_scope" for e in trace["events"])
                    counts[*key, "rejected"] += sum(e.get("admitted") is False for e in trace["events"])
                    paths["/".join((*key, "".join(opening)))] = trace
    dependencies = (Path(__file__), CASE, INITIAL, POLICY, question_outputs, Path(routing.__file__),
                    HERE / "scope_policy_refit.py", HERE.parent / "decision_ledger.py")
    return {"scope": "Adaptive offline transfer. Model scope projections are precomputed and read only when the policy checks the field. The author validates proposed public claims.",
            "source_sha256": {p.name if p != question_outputs else "scope-probe-metrics": sha256(p.read_bytes()).hexdigest()
                              for p in dependencies},
            "totals": {"/".join(k): v for k, v in counts.items()}, "paths": paths}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scope_probes", type=Path)
    args = parser.parse_args()
    print(json.dumps(assess(args.scope_probes), indent=2))
