"""Use truthful queried replies to separate routing from language failure."""
import argparse
from collections import Counter
from itertools import product
import json
from pathlib import Path

from probe import CONTINUATIONS, OPTIONS, cases, evaluate, select, serialize, summarize


def truth_reply(option, i, roles, truth, id_):
    raw = {"stance": "pass", "option": None}
    if option:
        raw = {"stance": "accept" if option in truth["allowed_by_role"][i] else "exclude", "option": option}
    return {"judgment": evaluate(serialize(raw), id_, roles[i], truth["allowed_by_role"][i], "query", option)}


def exact(roles, truth, open_rows, max_steps):
    rows = open_rows.copy()
    first = None
    prompts = []
    for step in range(max_steps+1):
        if summarize(roles, truth, rows)["correct"]:
            first = step
            break
        if step == max_steps:
            break
        claims = [r["judgment"]["admitted"] for r in rows if r["judgment"]["admitted"]]
        i, option = select(roles, claims, step)
        if not option:
            break
        rows.append(truth_reply(option, i, roles, truth, f"script-{step}"))
        prompts.append({"role": roles[i], "option": option})
    return {"first_certified": first, "questions": prompts, "final": summarize(roles, truth, rows)}


def report(path):
    rows = {r["id"]: r for r in map(json.loads, (path / "transcript.jsonl").read_text().splitlines())}
    results = {}
    for (family, variant), (roles, _, truth) in cases():
        opening = [rows[f"{family}/shared/open-0"], rows[f"{family}/{variant}/open-1"]]
        results[f"{family}/{variant}"] = exact(roles, truth, opening, CONTINUATIONS)
    menus = [[o for i, o in enumerate(OPTIONS) if mask & (1 << i)] for mask in range(1, 1 << len(OPTIONS))]
    grid = Counter()
    for left, right in product(menus, repeat=2):
        truth = {"allowed_by_role": [left, right], "joint_packages": sorted(set(left) & set(right))}
        arm = "agreement" if truth["joint_packages"] else "impasse"
        for a, b in product(left, right):
            roles = ("first", "second")
            opening = [truth_reply(a, 0, roles, truth, "script-open-0"),
                       truth_reply(b, 1, roles, truth, "script-open-1")]
            record = exact(roles, truth, opening, CONTINUATIONS)
            grid[(arm, record["first_certified"])] += 1
    return {"with_actual_openings_and_truthful_replies": results,
            "all_positive_opening_pairs": {arm: {str(n): grid[arm, n] for n in (*range(CONTINUATIONS+1), None)}
                                           for arm in ("agreement", "impasse")}}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path)
    print(json.dumps(report(parser.parse_args().run), indent=2))
