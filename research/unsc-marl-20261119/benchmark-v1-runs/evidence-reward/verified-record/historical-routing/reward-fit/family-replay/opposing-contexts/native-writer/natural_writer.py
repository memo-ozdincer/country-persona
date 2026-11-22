"""Run the matched UNIFIL states through a shared native final writer."""
import argparse
from hashlib import sha256
from itertools import product
import json
from pathlib import Path
import sys
from unittest.mock import patch

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import matched

base = matched.o.h.r.w.archived.base
D, BITS = matched.D, matched.BITS
CASE_PATH = matched.o.h.ARCHIVE.parents[2] / "crossbench/unifil-record.json"
WITNESS = HERE.parent / "triplets.json"
LIMIT = 150
OUT = HERE / "evidence"


def read(path):
    return json.loads(path.read_text())


def lines(path):
    return [json.loads(line) for line in path.read_text().splitlines()]


def setup():
    witness = read(WITNESS)["cases"]["unifil"]["asymmetric"]["first"]
    case = read(CASE_PATH)
    sources = [row for row in case["evidence"] if row["id"] in {"vote", "operative"}]
    cards = [next(row for row in case["evidence"] if row["id"] == name)
             for name in ("brazil", "china", "russia")]
    states = witness["state"]
    legal = np.flatnonzero(D.FINAL_LEGAL[witness["inventory"][1], 0, 0])
    reachable = sorted({state | BITS[card] for state in states for card in legal})
    requests = {}
    for mask in reachable:
        evidence = sources + [card for bit, card in zip(BITS[1:], cards) if mask & bit]
        payload = {"task": case["task"], "sources": [{k: row[k] for k in ("id", "text")} for row in evidence]}
        requests[mask] = {"messages": [
            {"role": "system", "content": "Write a standalone Council record using only the supplied sources. "
             "Use 125 to 140 words with an absolute maximum of 150. Include all material facts, "
             "with precise attribution and scoped agreement and disagreement when supported. "
             "Leave out a national explanation whose source is missing. Return only the record."},
            {"role": "user", "content": json.dumps(payload, ensure_ascii=False)}], "max_output_tokens": 280}
    return witness, case, requests


def plan():
    witness, _, requests = setup()
    paths = (Path(__file__), HERE / "protocol.md", CASE_PATH, WITNESS, Path(matched.__file__))
    return {"states": witness["state"], "inventory": witness["inventory"],
            "requests": [{"mask": mask, "request": row} for mask, row in requests.items()],
            "sha256": {p.name: sha256(p.read_bytes()).hexdigest() for p in paths}}


def collect(generate, directory):
    current = plan()
    if current != read(HERE / "plan.json"):
        raise ValueError("Writer plan has changed")
    for row in current["requests"]:
        response = generate(row["request"])
        base.suite.append(directory / "calls.jsonl", row | {"response": response})


def comparison(points):
    w, _, _ = setup()
    states, openings, holder = w["state"], w["openers"], w["inventory"][1]
    legal_queries = [np.flatnonzero(D.CHAIR_LEGAL[state]) for state in states]

    def action_summary(targets, replies):
        masks = [state | BITS[reply] for state, reply in zip(states, replies, strict=True)]
        raw = sum(points[mask] for mask in masks)
        cost = float(sum(D.QUERY_COST[t] + D.SEND_COST[r] for t, r in zip(targets, replies, strict=True)))
        return {"targets": targets, "replies": replies, "masks": masks, "released": raw,
                "cost": cost, "tail_net": raw - cost}

    def best(targets):
        targets = [int(t) for t in targets]
        result = matched.best_response(points, states, openings, holder, targets)
        return action_summary(targets, result["reply"])

    learned = action_summary([r["ask"] for r in w["learned"]], [r["reply"] for r in w["learned"]])
    fixed = {str(card): best([card if D.CHAIR_LEGAL[state, card] else 0 for state in states])
             for card in range(4)}
    adaptive = max((best(targets) for targets in product(*legal_queries)), key=lambda row: row["tail_net"])
    return {"learned": learned, "exact_fixed": fixed, "exact_adaptive": adaptive,
            "learned_margin_over_best_fixed": learned["tail_net"] - max(r["tail_net"] for r in fixed.values())}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("plan", "run"))
    if parser.parse_args().mode == "plan":
        print(json.dumps(plan(), ensure_ascii=False, indent=2))
    else:
        with patch.object(base.suite, "collect", collect), patch.object(
                base, "roster", return_value={"matched-unifil-native-writer": None}):
            base.run(OUT)
