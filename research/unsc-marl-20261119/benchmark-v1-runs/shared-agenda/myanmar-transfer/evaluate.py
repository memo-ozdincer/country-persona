"""Grade the established workshop rubric and replay its matched report decisions."""
import argparse
from itertools import product
import json
from math import isclose
from pathlib import Path
from statistics import mean

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RUBRIC = ROOT / "benchmark-kit/relay-final-rubric.json"
TRAIN = HERE.parent / "documentary/protected/reward-replay.json"
ARMS = ("scoped", "literal")
CONTRACTS = ("original", "second-card-required")
FEES = (.015, .06, .15, .25)
LINKS = (.45, .6, .8, .95)
PRIZES = (.8, 1., 1.2)


def read(path):
    return json.loads(path.read_text())


def grade(deck):
    rubric = read(RUBRIC)
    units = {r["id"] for r in rubric["units"]}
    marks = read(HERE / "marks.json")
    assert set(marks) == set(deck)
    maxwords = rubric["format"]["max_words"]
    out = {}
    for key, row in deck.items():
        review = marks[key]
        sources = {p["id"]: p["text"] for p in row["sources"]}
        statuses = {}
        for unit, item in review["units"].items():
            assert unit in units and set(item) == {"status", "reason", "source", "span"}
            status = item["status"]
            assert item["reason"] and status in ("met", "unmet", "uncertain")
            assert not item["span"] or item["span"] in row["text"]
            assert all(quote in sources[sid] and quote for sid, quote in item["source"])
            assert status != "met" or (item["span"] and item["source"])
            statuses[unit] = status
        assert set(statuses) == units
        guard = review["guard"]
        assert guard in ("clear", "failed", "uncertain") and review["guard_reason"]
        if guard == "failed":
            assert review["guard_span"] in row["text"] and review["guard_span"]
            assert review["guard_source"]
        assert all(quote in sources[sid] and quote for sid, quote in review["guard_source"])
        word_count = len(row["text"].split())
        valid = row["complete"] and row["heading_ok"] and word_count <= maxwords
        assert row["text"].splitlines()[0] == "Workshop status: agreement"
        result = {}
        for contract in CONTRACTS:
            readings = statuses.copy()
            if contract == CONTRACTS[1] and len(row["visible"]) == 1:
                readings["P2"] = "unmet"
            lower = sum(7 for v in readings.values() if v == "met")
            upper = sum(7 for v in readings.values() if v != "unmet")
            release = valid and guard == "clear"
            result[contract] = {"raw": [lower, upper], "released": lower if release else 0, "guard": guard,
                                "within_contract": bool(valid), "words": word_count, "units": readings}
        out[key] = result
    return out


def replay(scores):
    previous = read(TRAIN)["fitted_deltas"]
    fit = {arm: mean(previous[arm].values()) for arm in ARMS}
    receipts = sorted({"/".join(key.split("/")[:2]) for key in scores})
    assert len(receipts) == 4
    arms = {}
    for arm, contract in product(ARMS, CONTRACTS):
        comparisons = {}
        for fee in FEES:
            rows = []
            for key, p, w in product(receipts, LINKS, PRIZES):
                old = scores[f"{key}/1/{arm}"][contract]["released"]
                extra = scores[f"{key}/2/{arm}"][contract]["released"]
                raw = (extra-old)/70
                values = {"fixed-7": .1, "fixed-14": .2, "frozen-fit": fit[arm], "oracle": raw}
                gain = p*w*raw - fee
                alternatives = {"wait": False, "always-send": True}
                alternatives.update({name: p*w*v > fee for name, v in values.items()})
                outcomes = {}
                for name, send in alternatives.items():
                    actual_points = ((p*extra + (1-p)*old) if send else old) * w / 70
                    net = actual_points - w*old/70 - int(send)*fee
                    assert isclose(net, gain*send, abs_tol=1e-12)
                    outcomes[name] = dict(send=send, incremental_net=net, released=actual_points)
                assert all(s["incremental_net"] <= outcomes["oracle"]["incremental_net"] + 1e-12
                           for s in outcomes.values())
                rows.append(dict(case=key, link=p, priority=w, after_one=old, after_two=extra, policies=outcomes))
            comparisons[fee] = dict(rows=rows, mean={
                name: dict(net_gain=mean(r["policies"][name]["incremental_net"] for r in rows),
                           attempts=mean(r["policies"][name]["send"] for r in rows),
                           released=mean(r["policies"][name]["released"] for r in rows))
                for name in rows[0]["policies"]})
        arms[f"{arm}/{contract}"] = comparisons
    return dict(frozen_coefficients=fit, scores=scores, replays=arms)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("score", "replay"))
    mode = parser.parse_args().mode
    gradebook = grade(read(HERE / "deck.json"))
    print(json.dumps(gradebook if mode == "score" else replay(gradebook), indent=2, ensure_ascii=False))
