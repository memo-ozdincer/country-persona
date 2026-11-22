"""Replay the last agenda report with actual final-record rewards."""
import json
from math import isclose
from pathlib import Path
from statistics import mean
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))
import experiment as e
import opener_credit as opener

ARMS = ("wait", "send", "fixed-14", "fitted", "oracle")
WRITERS = ("free", "scoped", "literal")


def read(path):
    return json.loads(path.read_text())


def scores():
    new = read(HERE / "scores.json")["scores"]
    old = read(HERE.parent / "scores.json")["scores"]
    banks = {}
    for docket in e.DOCKETS:
        cases = sorted(key for key in new if key.startswith(docket + "-"))
        assert len(cases) == 2 and set(new) == set(old)
        banks[docket] = {name: {} for name in WRITERS}
        for case in cases:
            for name in WRITERS:
                if name == "free":
                    values = tuple(old[case][str(c)]["released_70"] for c in (1, 2))
                else:
                    values = tuple(new[case][str(c)][name]["released_70"] for c in (1, 2))
                banks[docket][name][case] = values
    return banks


def open_mass(scene, opener_actions, action):
    # The first delivery and public proof must happen, and the later role must hold the card.
    value = 0.
    for i, menu in enumerate(e.MENUS):
        assert opener_actions[i] in menu
        if opener_actions[i] == action:
            prob = sum(scene["p"][i, j] for j, allowed in enumerate(e.MENUS) if action in allowed)
            value += prob * scene["links"][0, action-1] * e.FIRST_ONLY
    return value


def fit_delta(bank):
    # Least-squares intercept on exact realized increments conditional on delivery.
    scaled = [(two-one)/70 for one, two in bank.values()]
    theta = mean(scaled)
    assert isclose(sum(theta-target for target in scaled), 0., abs_tol=1e-12)
    return theta


def evaluate(scene, action, where, fee, mass, bank, fitted_delta):
    chance = float(scene["links"][1, action - 1])
    priority = float(scene["prizes"][action - 1])
    result = {}
    for case, (base, follow) in bank.items():
        change = (follow - base) / 70
        preferences = {"wait": False, "send": True, "fixed-14": chance * priority * .2 > fee,
                       "fitted": chance * priority * fitted_delta > fee,
                       "oracle": chance * priority * change > fee}
        ends = {}
        for arm, send in preferences.items():
            marginal = chance * priority * change - fee if send else 0.
            released = ((chance * follow + (1 - chance) * base) if send else base) / 70
            independently_dispatched = released * priority - priority * base / 70 - int(send) * fee
            assert isclose(marginal, independently_dispatched, abs_tol=1e-12)
            ends[arm] = dict(send=send, released_gain=mass * chance * priority * change * send,
                             net_gain=mass * marginal, attempts=mass * send)
        assert all(r["net_gain"] <= ends["oracle"]["net_gain"] + 1e-10 for r in ends.values())
        result[case] = ends
    return dict(docket=where, fee=fee, mass=mass, cases=result)


def run():
    banks = scores()
    arms = {}
    for name in WRITERS:
        arms[name] = {docket: fit_delta(banks[opponent][name])
                      for docket, opponent in zip(e.DOCKETS, reversed(e.DOCKETS), strict=True)}
    previous = read(e.HERE / "opener-credit.json")["evaluation"]["0.06"]["held"]
    held = e.settings(True)
    result = {}
    for name, fitted in arms.items():
        fees = {}
        for fee in opener.FEES:
            scenes = []
            for scene, snapshot in zip(held, previous, strict=True):
                rows = []
                for action, docket in enumerate(e.DOCKETS, 1):
                    mass = open_mass(scene, snapshot["tables"]["accounting-fit"], action)
                    rows.append(evaluate(scene, action, docket, fee, mass, banks[docket][name], fitted[docket]))
                scenes.append(rows)
            summary = {}
            for arm in ARMS:
                parts = [{indicator: sum(mean(c[arm][indicator] for c in branch["cases"].values())
                                         for branch in agenda)
                          for indicator in ("net_gain", "released_gain", "attempts")} for agenda in scenes]
                summary[arm] = {key: mean(row[key] for row in parts) for key in parts[0]}
            fees[fee] = dict(summary=summary, held=scenes)
        result[name] = fees
    files = (Path(__file__), HERE / "reward-replay-protocol.md", HERE / "scores.json",
             HERE.parent / "scores.json", e.HERE / "opener-credit.json")
    return dict(fitted_deltas=arms, banks=banks,
                hashes={str(path.relative_to(e.RELEASE.parent)): e.digest(path) for path in files},
                writers=result)


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
