"""Select a complete scope set, with a same-family wording reserve."""
import argparse
from collections import Counter
import json
from pathlib import Path
import sys

from scope_questions import RESERVE, REFERENCE, CASE, HERE, ENTAILMENT, clause_control, load, runner

sys.path.insert(0, str(ENTAILMENT))
import field_panel

LOCK = HERE / "scope-sets-lock.json"
SCOPE_GROUPS = {
    "focused-or-staged": ("broad",),
    "staged-or-broad": ("focused",),
    "broad-only": ("focused", "staged"),
    "all": (),
}
LABELS = "ABCD"
OPTIONS = {
    "focused-or-staged": "Allow focused-only or a staged expansion. An expanded first stage violates the scope condition.",
    "staged-or-broad": "Allow a staged expansion or an expanded first stage. Focused-only violates the scope condition.",
    "broad-only": "Allow only an expanded first stage. Both focused-only and staged expansion violate the scope condition.",
    "all": "Allow focused-only, staged expansion and an expanded first stage.",
}
UNRESTRICTED = "All timings for the wider remit are acceptable, including no expansion. Seek negotiations for an agreement, with a dedicated verification review if the Conference on Disarmament leads."
RESERVE_TWO = {
    "japan": "Preserve the treaty remit for the opening text. A wider remit can appear in a second phase if useful. Do not widen the opening text. Follow-up should remain with the Conference on Disarmament.",
    "china-overlap": "The text is unacceptable if it leaves the wider remit out altogether. A firm second-phase commitment is enough to meet our scope requirement. Seek negotiations on the agreement.",
    "china-impasse": "The wider remit is a condition for accepting the very first phase. A promise to cover it later leaves the condition unsatisfied. Seek negotiations on the agreement.",
}


def panels():
    return {"original": load(CASE)["cards"], "reworded": {**RESERVE, "control": UNRESTRICTED},
            "fresh-wording": RESERVE_TWO}


def suite():
    for panel, cards in panels().items():
        for card, mandate in cards.items():
            for order, values in enumerate((list(OPTIONS), list(reversed(OPTIONS)))):
                labels = dict(zip(LABELS, (OPTIONS[k] for k in values), strict=True))
                fields = {"private_mandate": mandate, "scope_choices": labels}
                prompt = ("Read only the scope and timing of broader coverage in the mandate. "
                          "Focused-only never expands scope. Staged expansion expands it only in a second phase. "
                          "An expanded first stage expands it immediately. Ignore the forum, product and review. "
                          "Select the option that gives the complete set allowed by the mandate. Output its letter only.")
                yield {"id": f"{panel}/{card}/{order}", "values": values, "labels": LABELS,
                       "messages": [{"role": "system", "content": prompt},
                                    {"role": "user", "content": json.dumps(fields)}]}


def score(rows):
    winners = {}
    for plan in suite():
        logits = rows[plan["id"]]["label_logits"]
        highest = max(logits)
        ordered = [k for k, logit in zip(plan["values"], logits, strict=True) if logit == highest]
        winners[plan["id"]] = ordered[0] if len(ordered) == 1 else None
    projections, tags, counts, paths = {}, {}, Counter(), {}
    for panel, cards in panels().items():
        prediction = {}
        for card in cards:
            hits = [winners[f"{panel}/{card}/{order}"] for order in range(2)]
            stable = hits[0] if hits[0] == hits[1] else None
            expected = REFERENCE.get(card, set())
            exclusions = set(SCOPE_GROUPS[stable]) if stable else set()
            prediction[card] = exclusions
            correct = stable is not None and exclusions == expected
            counts[panel, "scope", "correct" if correct else "abstain" if stable is None else "wrong"] += 1
            projections[f"{panel}/{card}"] = {"rejected_scopes": sorted(exclusions),
                                               "exact": correct, "winner": stable, "pair": hits}
            tags[f"{panel}/{card}"] = sorted(expected)
        for key, row in clause_control.evaluate(prediction)["paths"].items():
            paths[f"{panel}/{key}"] = row
            case = key.split("/")[0]
            counts[panel, case, row["public"]["state"]] += 1
            counts[panel, case, "slots"] += row["slots"]
            counts[panel, case, "rejected"] += sum(event.get("status") == "rejected" for event in row["events"])
    return {"totals": {"/".join(k): v for k, v in counts.items()},
            "projections": projections, "reference_exclusions": tags, "paths": paths}


def digests():
    paths = (Path(__file__), CASE, HERE / "scope_questions.py", HERE / "scope_model.py",
             HERE / "clause_control.py", HERE.parent / "decision_ledger.py", HERE / "evidence/metrics.json",
             ENTAILMENT / "field_panel.py")
    return {str(p.resolve().relative_to(HERE.parents[1])): runner.digest(p) for p in paths}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("lock", "run", "replay"))
    parser.add_argument("output", type=Path, nargs="?")
    parser.add_argument("--model", type=Path)
    args = parser.parse_args()
    if args.mode == "lock":
        assert len(list(suite())) == 20
        with LOCK.open("x") as fh:
            json.dump({"calls": 20, "hashes": digests(),
                       "scope": "Four preregistered scope shapes, two label orders, one unrestricted control. Recovered exclusions use the same publication and authored validation rules."}, fh, indent=2)
            fh.write("\n")
        return
    assert load(LOCK)["hashes"] == digests()
    if args.mode == "run":
        field_panel.suite, field_panel.score = suite, score
        field_panel.main(args.model, args.output)
        return
    file = args.output / "predictions.jsonl"
    assert load(args.output / "complete.json") == {"records": 20, "sha256": runner.digest(file)}
    records = list(map(json.loads, file.read_text().splitlines()))
    for example, actual in zip(suite(), records, strict=True):
        assert all(actual[k] == v for k, v in example.items())
    result = score({x["id"]: x for x in records})
    assert json.loads(json.dumps(result)) == load(args.output / "metrics.json")
    print(json.dumps({"input_hashes": len(digests()), "records": 20,
                      "exact_routing_paths": len(result["paths"])}, indent=2))


if __name__ == "__main__":
    main()
