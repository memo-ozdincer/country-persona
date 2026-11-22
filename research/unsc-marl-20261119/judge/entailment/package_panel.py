"""Fixed role-package contrast evaluation with downstream routing replay."""
import argparse
from collections import Counter
from hashlib import sha256
from itertools import product
import json
from pathlib import Path
import sys

import run as judge

HERE = Path(__file__).resolve().parent
CARDS = HERE / "package-cards.json"
PROSE = HERE.parents[1] / "crossbench/disclosure/clarify/routing/live/prose"
sys.path.insert(0, str(PROSE))
from study import describe, dispatch, source_paths, project, guarded, restore
from transfer import CONTRAST

ELIGIBLE = "This package meets all explicit requirements of the private mandate."
INELIGIBLE = "This package fails at least one explicit requirement of the private mandate."


def inputs():
    docs = json.loads(CARDS.read_text())
    paths = source_paths()
    for item in docs["cases"]:
        name = item["family"]
        case = json.loads(paths[name].read_text())
        yield name, case, item


def codec(obj):
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"))


def suite():
    for family, case, item in inputs():
        for index, card in enumerate(item["cards"]):
            for option in case["options"]:
                option_id = option["id"]
                source = (f"Private mandate: {card['prose']}\n"
                          f"Offered package {option_id}: {describe(option)}")
                for invert in (False, True):
                    claims = (INELIGIBLE, ELIGIBLE) if invert else (ELIGIBLE, INELIGIBLE)
                    body = {
                        "source": source,
                        "highlighted_quote": source,
                        "candidate_claims": dict(zip(("A", "B"), claims, strict=True)),
                    }
                    yield {
                        "id": f"{family}/{index}/{option_id}/{int(invert)}",
                        "support_code": "B" if invert else "A",
                        "messages": [{"role": "system", "content": CONTRAST},
                                     {"role": "user", "content": codec(body)}],
                    }


def decisions(rows):
    scores = {}
    for plan in suite():
        a, b = rows[plan["id"]]["label_logits"]
        margin = a-b if plan["support_code"] == "A" else b-a
        scores.setdefault(plan["id"].rsplit("/", 1)[0], []).append(margin)
    return {name: {
        "margins": pair,
        "accept": True if all(x > 0 for x in pair) else False if all(x < 0 for x in pair) else None,
    } for name, pair in scores.items()}


def evaluate(result):
    paths = source_paths()
    actor = guarded(restore(json.loads(paths["policy"].read_text())))
    counts = Counter()
    traces = {}
    menus = {}
    for family, case, item in inputs():
        labels = [o["id"] for o in case["options"]]
        expected = tuple(project(case["options"], card["expected"]) for card in item["cards"])
        assert bool(expected[0] & expected[1]) == (item["outcome"] == "agreement")
        observed = []
        for index, gold in enumerate(expected):
            options = [result[f"{family}/{index}/{label}"] for label in labels]
            menu = None if any(r["accept"] is None for r in options) else sum(
                (1 << i) for i, entry in enumerate(options) if entry["accept"])
            observed.append(menu)
            menus[f"{family}/{index}"] = {"observed": menu, "expected": gold,
                                          "exact": menu == gold}
            for i, (label, entry) in enumerate(zip(labels, options, strict=True)):
                actual = bool(gold & (1 << i))
                entry["expected"] = actual
                code = ("abstain" if entry["accept"] is None else
                        "correct" if entry["accept"] == actual else "wrong")
                counts[family, "eligible" if actual else "ineligible", code] += 1
        correct_state = "AGREEMENT_POSSIBLE" if item["outcome"] == "agreement" else "IMPASSE"
        openings = product(*([label for i, label in enumerate(labels) if mask & (1 << i)] for mask in expected))
        for first in openings:
            for mode in ("authored", "judge"):
                for arm in ("script", "learned"):
                    local = expected if mode == "authored" else observed
                    trace = dispatch(case, first, local, expected, arm, actor)
                    key = family, mode, arm
                    counts[*key, "presentations"] += 1
                    counts[*key, "certified"] += trace["state"] == correct_state
                    counts[*key, "rejected"] += len(trace["rejected"])
                    traces["/".join((*key, "".join(first)))] = trace
    return {"totals": {"exact_menus": sum(m["exact"] for m in menus.values()), "roles": len(menus),
                       "decisions": len(result), "replayed_paths": len(traces)},
            "metrics": {"/".join(k): v for k, v in counts.items()}, "decisions": result,
            "menus": menus, "traces": traces}


def score(rows):
    return evaluate(decisions(rows))


def dependencies():
    return (HERE/"package_panel.py", CARDS, HERE/"transfer.py", PROSE/"study.py",
            *source_paths().values(),
            PROSE.parent/"episode.py",
            *(PROSE.parents[1]/n for n in ("environment.py", "joint.py", "guard.py", "sanctions.py")))


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("model", type=Path)
    p.add_argument("output", type=Path)
    args = p.parse_args()
    judge.suite = suite
    judge.score = score
    judge.main(args.model, args.output)
    (args.output/"package-lock.json").write_text(codec({
        str(path): sha256(path.read_bytes()).hexdigest() for path in dependencies()}) + "\n")
