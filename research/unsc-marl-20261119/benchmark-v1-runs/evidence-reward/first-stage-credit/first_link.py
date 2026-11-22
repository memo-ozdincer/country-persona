"""Verify whole-record composition and first-link decision cost sensitivity."""
from collections import Counter
from hashlib import sha256
from pathlib import Path

import ledger_features as l

HERE = Path(__file__).resolve().parent
E = l.E
RATES = (.02, .04, .08, .80)
SEND = .035


def margin(features, weights):
    sign = features[-1]
    values = features[:-1]
    block = tuple(v*sign for v in values) + tuple(v*(1-sign) for v in values)
    return sum(w*v for w,v in zip(weights, block, strict=True))


def with_erasure(before, shipped, source_rate, new_rate):
    # The saved delivery average includes cost paid even on erasure.
    return [b + (new_rate/source_rate)*(s-b-(SEND if i == 1 else 0.)) + (SEND if i == 1 else 0.)
            for i, (b, s) in enumerate(zip(before, shipped, strict=True))]


def payoff(metrics):
    return metrics[0]/70 - metrics[1]


def run():
    ledger = E.read(HERE/"ledger-fit.json")
    covariates = E.read(HERE/"ledger-features.json")["features"]["held"]
    table = E.read(HERE/"reward-table.json")["paths"]["held"]
    original = E.read(l.signed.SIGNED/"roster.json")["held"]
    base = E.read(HERE.parent/"record-replay/scores.json")["rates"]["0.8"]["arms"]["value"]
    ranked = {}
    for rate in RATES:
        sums = {name: Counter(expected_released_70=0., cost=0., followups=0., sends=0., net=0.)
                for name in ("learned", "exact")}
        details = {}
        for item in original:
            key = item["id"]
            pay = table[key]
            x = list(covariates[key])
            assert x[-2] == item["delivery"]
            x[-2] = rate
            before = pay["guarded_outcome"]["P"]
            actual = pay["guarded_outcome"][pay["truthful_action"]]
            sent = with_erasure(before, actual, item["delivery"], rate)
            policy = {"learned": margin(x, ledger["weights"]["ledger_only"]) > 0.,
                      "exact": payoff(sent) > payoff(before) + 1e-10}
            details[key] = {"send": policy, "send_value": payoff(sent), "pass_value": payoff(before)}
            if rate == .80:
                for mode, arm in (("learned", "ledger_only"), ("exact", "exact")):
                    assert policy[mode] == (ledger["held"]["rows"][key][arm]["action"] != "P")
            for name, speaks in policy.items():
                selected = sent if speaks else before
                for field, value in zip(("expected_released_70", "cost", "followups"), selected, strict=True):
                    sums[name][field] += value
                sums[name]["sends"] += speaks
                sums[name]["net"] += payoff(selected)
        regret = sums["exact"]["net"] - sums["learned"]["net"]
        assert regret >= -1e-9
        ranked[str(rate)] = {"arms": sums, "regret": regret, "rows": details}
    assert abs(ranked["0.8"]["arms"]["learned"]["expected_released_70"] - base["released_70"]) < 1e-9
    assert abs(ranked["0.8"]["arms"]["learned"]["followups"] - base["followup_questions"]) < 1e-9
    files = (Path(__file__), HERE/"first-link-protocol.md", HERE/"ledger-fit.json", HERE/"ledger-features.json",
             HERE/"reward-table.json", HERE.parent/"record-replay/scores.json")
    return {"rates": ranked, "second_delivery": .8,
            "sha256": {p.name: sha256(p.read_bytes()).hexdigest() for p in files}}


if __name__ == "__main__":
    E.emit(run())
