"""Apply exact-span review and replay policy differences through full records."""
import argparse
from hashlib import sha256
from pathlib import Path
import json
from math import isclose
import re

import memo

HERE = Path(__file__).resolve().parent
ARMS = ("literal", "scoped")
POLICIES = ("fixed", "rank-fit", "switch-32")


def read(name):
    return json.loads((HERE / name).read_text())


def scores(deck):
    marks = read("marks.json")
    rubric = read("rubric.json")
    units = {a["id"]: a["points"] for a in rubric["axis"]}
    assert sum(units.values()) == 70
    assert deck.keys() == marks.keys()
    result = {}
    for key, row in deck.items():
        mark = marks[key]
        evidence = {d["id"]: d["text"] for d in row["history"]}
        evidence["summary"] = json.dumps(row["facts"], ensure_ascii=False)
        evidence["scope"] = memo.SCOPE
        evidence["heading"] = f'Workshop disposition: {row["facts"]["checked_disposition"]}'
        text = row["answer"]
        grades = mark["units"]
        assert grades.keys() == units.keys()
        for unit in (*grades.values(), mark["guard"]):
            assert unit["reason"]
            assert not unit["span"] or unit["span"] in text
            for source, quote in unit["sources"]:
                assert quote and quote in evidence[source]
        assert all(r["status"] in ("met","unmet","uncertain") for r in grades.values())
        assert all(r["span"] and r["sources"] for r in grades.values() if r["status"] == "met")
        guard = mark["guard"]["status"]
        assert guard in ("clear", "failed", "uncertain")
        assert guard == "clear" or (mark["guard"]["span"] and mark["guard"]["sources"])
        words = len(text.split())
        exact = text.splitlines()[0] == evidence["heading"]
        duplicate = re.search(r"(?im)^\s*workshop disposition\s*:", row["paragraph"])
        ready = bool(exact and not duplicate and row["paragraph"].strip() and words <= rubric["word_limit"] and row["complete"])
        release = ready and guard == "clear"
        lower = sum(units[k] for k, v in grades.items() if v["status"] == "met")
        upper = sum(units[k] for k, v in grades.items() if v["status"] != "unmet")
        released = lower if release else 0
        settled = row["facts"]["checked_disposition"] != "unresolved"
        result[key] = dict(words=words, format_ok=ready, guard=guard, raw=[lower, upper], released=released,
                           settled_release=released if settled else 0, settled=settled,
                           full=float(released == 70), input_tokens=row["input_tokens"], output_tokens=row["output_tokens"])
    return result


def switching():
    import history_prior as history
    old = memo.s.read(HERE.parent / "history-prior.json")
    _, regimes = memo.model()
    infos = [memo.receive.aggregate(data, choices["fixed"][0]) for _, data, choices in regimes]
    frequencies = history.mass_distribution(infos, True)
    post, mass = history.likelihoods(frequencies)[0][32]
    switch = mass[post > .5].sum(0)
    for i, (name, _, choices) in enumerate(regimes):
        raw = {a: choices[a][1]["net"] for a in ("fixed", "rank-fit")}
        archived = old["cases"]["space-198"]["history"]["own+messages"]["horizons"]["32"]["policies"]
        result = raw["fixed"] + switch[i]*(raw["rank-fit"]-raw["fixed"])
        assert isclose(result, archived["posterior-switch"][name], abs_tol=1e-10)
    return dict(zip((key for key, _, _ in regimes), switch.tolist(), strict=True))


def replay(rows, switch):
    keys = ("released", "settled_release", "full", "settled", "input_tokens", "output_tokens")
    plan = read("plan.json")
    status = {}
    for regime, pairs in plan["pairs"].items():
        masses = {policy: {} for policy in ("fixed", "rank-fit")}
        for key in masses:
            column = "fixed" if key == "fixed" else "fitted"
            for case in pairs:
                view = case[column]
                masses[key][view] = masses[key].get(view, 0.)+case["mass"]
            assert isclose(sum(masses[key].values()), 1.)
        out = {}
        for arm in ARMS:
            averages = {policy: {metric: sum(p*rows[f"{view}/{arm}"][metric] for view, p in counts.items())
                                 for metric in keys} for policy, counts in masses.items()}
            paired = {metric: sum(p["mass"]*(rows[f'{p["fitted"]}/{arm}'][metric]-rows[f'{p["fixed"]}/{arm}'][metric])
                                  for p in pairs) for metric in keys}
            assert all(isclose(averages["rank-fit"][k]-averages["fixed"][k], paired[k], abs_tol=1e-9) for k in keys)
            averages["switch-32"] = {key: averages["fixed"][key]+switch[regime]*paired[key] for key in keys}
            out[arm] = dict(means=averages, paired_rank_minus_fixed=paired)
        status[regime] = out
    mix = {a: {policy: {k: sum(d[a]["means"][policy][k] for d in status.values())/len(status) for k in keys}
              for policy in POLICIES} for a in ARMS}
    release = read("plan.json")
    control = memo.s.read(HERE.parent/"ranking.json")
    rates = {"balanced": "balanced", "uniform": "uniform-stress"}
    fees = {r: next(row["scores"]["fixed"]["peer_rate"] for row in control["results"][m]["space-reserved"]["rows"]
                    if row["case"] == memo.DRAW)*memo.FEES for r, m in rates.items()}
    assert len(release["views"])*len(ARMS) == len(rows)
    return dict(switch_by_regime=switch, conditional=status, equal_mixture=mix, peer_fee_unchanged=fees,
                receipts=len(release["views"]), stamps={name: sha256((HERE/name).read_bytes()).hexdigest()
                                                      for name in ("rubric.json","plan.json","deck.json","marks.json")})


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("mode", choices=("score","replay"))
    mode = cli.parse_args().mode
    rows = scores(read("deck.json"))
    print(json.dumps(rows if mode == "score" else replay(rows, switching()), indent=2, ensure_ascii=False))
