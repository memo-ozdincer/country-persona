"""Validate live judge replies and measure their downstream routing effects."""
import argparse
import importlib.util
import json
from itertools import combinations
from pathlib import Path
import re
from statistics import mean
import sys

import numpy as np

from pair_review_live import HERE, cases, digest, t

PARENT = HERE.parent
spec = importlib.util.spec_from_file_location("crosscase_floor_review", PARENT / "transfer.py")
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)
READ = t.wire.n.read
TEAM = audit.TEAM
EPS = audit.EPS


def legal_scores(criteria, base):
    weights = [c["weight"] for c in criteria]
    return {0} | {base + sum(part) for n in range(len(weights) + 1) for part in combinations(weights, n)}


def validate(arm, packet, response):
    if response["termination"] != "complete":
        raise ValueError("incomplete")
    text = response["text"]
    if arm == "numeric":
        if not re.fullmatch(r"\d{1,2}", text):
            raise ValueError("invalid integer format")
        score = int(text)
        if score not in legal_scores(packet["criteria"], packet["public_base"]):
            raise ValueError("score is outside the rubric lattice")
        return {"accepted": True, "score": score}
    try:
        obj = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError("invalid JSON") from exc
    if not isinstance(obj, dict) or set(obj) != {"guard", "units", "fault"} or obj["guard"] not in ("C", "F", "U"):
        raise ValueError("invalid verdict schema or guard")
    units = obj["units"]
    if not isinstance(units, list) or len(units) != len(packet["criteria"]):
        raise ValueError("incomplete criterion list")
    source, answer = packet["sources"], packet["record"]
    fault = obj["fault"]
    if not isinstance(fault, str) or (fault != "" if obj["guard"] == "C" else not fault.strip() or fault not in answer):
        raise ValueError("invalid fault quote")
    statuses, lower = {}, packet["public_base"]
    for criterion, item in zip(packet["criteria"], units, strict=True):
        if not isinstance(item, list) or len(item) != 5 or not all(isinstance(value, str) for value in item):
            raise ValueError("invalid criterion shape")
        item_id, status, quote, block, witness = item
        if item_id != criterion["id"] or status not in ("M", "N", "U"):
            raise ValueError("invalid criterion ID, order or status")
        if status == "M":
            if not quote.strip() or quote not in answer:
                raise ValueError("record quote mismatch for " + item_id)
            if block not in source or not witness.strip() or witness not in source[block]:
                raise ValueError("source quote mismatch for " + item_id)
            lower += criterion["weight"]
        elif (quote, block, witness) != ("", "", ""):
            raise ValueError("quotes supplied for a non-met criterion")
        statuses[item_id] = status
    uncertain = obj["guard"] == "U" or "U" in statuses.values()
    released = lower if obj["guard"] == "C" else 0
    return {"accepted": not uncertain, "score": released, "guard": obj["guard"],
            "statuses": statuses, **({"reason": "uncertain reading"} if uncertain else {})}


def grades():
    packets = cases()
    actual = READ(HERE / "verified.json")
    assert set(actual["calls"]) == {f"{name}/{arm}" for name in packets for arm in ("quoted", "numeric")}
    expected = {name: row[3] for name, row in READ(PARENT / "plan.json")["banks"].items() if name in packets}
    rows = {}
    for key, reply in actual["calls"].items():
        case, arm = key.split("/")
        try:
            verdict = validate(arm, packets[case], reply)
        except ValueError as exc:
            verdict = {"accepted": False, "reason": str(exc)}
        if verdict["accepted"]:
            verdict["matches_archive"] = verdict["score"] == expected[case]
        rows[key] = verdict | {k: reply[k] for k in ("input_tokens", "output_tokens", "elapsed_seconds")}
    return {"archived_grades": expected, "verdicts": rows, "input_sha256": digest(HERE / "verified.json")}


def reroute(row, points, grade):
    law, _ = audit.a.laws()[row["law"]]
    priors = [law] if row["prior_information"] == "exact" else audit.vertices(row["law"])
    opening = tuple(np.array(desk) for desk in row["opening"])
    visible = points.copy()
    visible[[3, 7]] = np.nan
    choices, _ = audit.pick(visible, grade, priors, opening, {})
    _, policy, eligible = choices[TEAM]
    mixed = None
    if not eligible:
        scenarios = audit.forecast_data(visible, grade, priors, opening)
        mixed, _, _ = audit.full_search(audit.o.fit.MAPS, scenarios)
    oracle = audit.o.controls(points, audit.o.opening(*opening, law), law, opening)
    return audit.held(policy if mixed is None else mixed, points, law, opening, oracle, stochastic=mixed is not None)


def replay():
    old = READ(PARENT / "results.json")
    banks = READ(PARENT / "plan.json")["banks"]
    replay_rows = READ(PARENT / "review-value.json")
    observed = grades()
    arms = ("numeric", "quoted")
    seen = {}
    previous = {(r["case"], r["law"], r["prior_information"], r["review_offset"]): r
                for r in old["rows"]}
    output = []
    for pair in replay_rows["pairs"]:
        case, label, info, offset = (pair[k] for k in ("case", "law", "prior_information", "offset"))
        row = previous[case, label, info, offset]
        start = row["updated"][TEAM]
        assert start == pair["before"]
        measures, reports = {}, {}
        for arm in arms:
            verdict = observed["verdicts"][f"{case}/{arm}"]
            if not verdict["accepted"]:
                reports[arm] = None
                measures[arm] = start
                continue
            grade = verdict["score"]
            reports[arm] = grade
            key = case, label, info, grade
            if key not in seen:
                matching = next((previous[case, label, info, delta]["updated"][TEAM]
                                 for delta in (-7, 0, 7) if grade == np.clip(banks[case][3] + delta, 0, 70)), None)
                seen[key] = matching if matching is not None else reroute(row, np.array(banks[case], float), grade)
            measures[arm] = seen[key]
        output.append({"case": case, "law": label, "prior_information": info, "offset": offset,
                       "observed_model_grades": reports, "original": start,
                       "exact_counterfactual": pair["clean_review"], **measures})
    assert len(output) == len(replay_rows["pairs"]) == 23
    summary = {}
    for key in ("original", "numeric", "quoted", "exact_counterfactual"):
        net = [row[key]["net"] - row["original"]["net"] for row in output]
        summary[key] = {"net_mean_over_original": mean(net), "wins": sum(v > EPS for v in net),
                        "ties": sum(abs(v) <= EPS for v in net), "losses": sum(v < -EPS for v in net),
                        "below_informed_silence": sum(row[key]["over_informed_silence_quality"] < -EPS for row in output)}
    pins = (Path(__file__).resolve(), HERE / "verified.json", HERE / "plan.json", PARENT / "results.json",
            PARENT / "review-value.json", PARENT / "plan.json")
    return {"grades": observed, "summary": summary, "rows": output,
            "sha256": {str(path.relative_to(PARENT)): digest(path) for path in pins}}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("grades", "replay"))
    print(json.dumps({"grades": grades, "replay": replay}[parser.parse_args().mode](), ensure_ascii=False, indent=2))
