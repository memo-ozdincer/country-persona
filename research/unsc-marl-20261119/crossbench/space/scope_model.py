"""Test scope-only interpretation under both label orders, then replay clause disclosure."""
import argparse
from collections import Counter
import json
from pathlib import Path
import sys

import clause_control

HERE = Path(__file__).resolve().parent
ENTAILMENT = HERE.parents[1] / "judge/entailment"
sys.path.insert(0, str(ENTAILMENT))
import run as runner

CASE = HERE / "case.json"
LOCK = HERE / "scope-preregistered.json"
SCOPE = {"focused": "Keep the existing treaty focus with no broader second stage.",
         "staged": "Start with the existing treaty focus and explicitly assign broader issues to a second stage.",
         "broad": "Include broader issues in the first stage."}
REFERENCE = {"japan": {"broad"}, "china-overlap": {"focused"},
             "china-impasse": {"focused", "staged"}}
SYSTEM = (
    "Read this fictional private mandate and classify only its scope requirement. "
    "Assume all requirements about the product, forum and verification review are met. "
    "Choose the statement that is supported by the mandate. A scoped reading must respect "
    "both what can be deferred to a later stage and what is mandatory now. "
    "Respond with a single letter A or B."
)


def load(path):
    return json.loads(path.read_text())


def suite():
    for card, mandate in load(CASE)["cards"].items():
        for name, description in SCOPE.items():
            claims = ("The scope fails the mandate's scope requirement.",
                      "The scope satisfies the mandate's scope requirement.")
            for reverse in (False, True):
                tagged = dict(zip("AB", claims[::-1] if reverse else claims, strict=True))
                payload = {"private_mandate": mandate, "scope": description, "choose": tagged}
                yield {"id": f"{card}/{name}/{int(reverse)}", "excluded_code": "B" if reverse else "A",
                       "messages": [{"role": "system", "content": SYSTEM}, {
                           "role": "user", "content": json.dumps(payload, ensure_ascii=False),
                       }]}


def score(rows):
    decisions, stats = {}, Counter()
    refined = {card: set() for card in REFERENCE}
    for card, expected in REFERENCE.items():
        for scope in SCOPE:
            a, b = rows[f"{card}/{scope}/0"]["label_logits"]
            c, d = rows[f"{card}/{scope}/1"]["label_logits"]
            margins = (a - b, d - c)
            excludes = True if min(margins) > 0 else False if max(margins) < 0 else None
            if excludes:
                refined[card].add(scope)
            actual = scope in expected
            label = "abstain" if excludes is None else "correct" if excludes == actual else "wrong"
            stats[f"decision/{label}"] += 1
            decisions[f"{card}/{scope}"] = {"margins": margins, "excludes": excludes, "expected": actual}
    replays = clause_control.evaluate(refined)
    for key, row in replays["paths"].items():
        case = key.split("/")[0]
        stats[f"{case}/{row['public']['state']}"] += 1
        stats[f"{case}/slots"] += row["slots"]
        stats[f"{case}/rejected"] += sum(e.get("status") == "rejected" for e in row["events"])
        stats[f"{case}/checks"] += sum(e["type"] == "model_scope_check" for e in row["events"])
    return {"totals": dict(stats), "decisions": decisions,
            "published_scope_candidates": {card: sorted(excluded) for card, excluded in refined.items()},
            "paths": replays["paths"]}


def hashes():
    return {str(p.resolve().relative_to(HERE.parents[1])): runner.digest(p) for p in (
        Path(__file__), CASE, HERE / "clause_control.py", HERE.parent / "decision_ledger.py",
        HERE / "evidence/metrics.json", HERE / "evidence/clause-control.json", ENTAILMENT / "run.py")}


def replay(output):
    p = output / "predictions.jsonl"
    records = list(map(json.loads, p.read_text().splitlines()))
    assert load(output / "complete.json") == {"records": 18, "sha256": runner.digest(p)}
    for example, row in zip(suite(), records, strict=True):
        assert all(row[k] == v for k, v in example.items())
    result = score({r["id"]: r for r in records})
    assert json.loads(json.dumps(result)) == load(output / "metrics.json")
    print(json.dumps({"input_hashes": len(hashes()), "predictions": 18, "routing_paths": len(result["paths"])}, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("lock", "run", "replay"))
    parser.add_argument("output", type=Path, nargs="?")
    parser.add_argument("--model", type=Path)
    args = parser.parse_args()
    if args.mode == "lock":
        assert len(list(suite())) == 18
        with LOCK.open("x") as out:
            json.dump({"assessment": "One exposed family. Order-stable exclusions only. Unknown projections produce no exclusion. Charge either scope check one logical slot and replay the same subsequent publication script.",
                       "calls": 18, "hashes": hashes()}, out, indent=2)
            out.write("\n")
        return
    assert load(LOCK)["hashes"] == hashes()
    if args.mode == "run":
        runner.suite, runner.score = suite, score
        runner.main(args.model, args.output)
    else:
        replay(args.output)


if __name__ == "__main__":
    main()
