"""Recover stage restrictions with separate tests of obligation and prohibition."""
import argparse
from collections import Counter
import json
from pathlib import Path

from scope_model import CASE, HERE, ENTAILMENT, REFERENCE, clause_control, load, runner

LOCK = HERE / "scope-questions-lock.json"
RESERVE = {
    "japan": "You are drafting in a simulated workshop. A text with the established treaty focus can proceed. Any wider remit is for a subsequent phase. An initial text that widens the remit is unacceptable. Leave all follow-up to the Conference on Disarmament. Either a study or talks, and either choice on review, is fine.",
    "china-overlap": "You are drafting in a simulated workshop. A commitment to cover the wider remit is indispensable, but putting that remit into the next phase would satisfy this requirement. Seek negotiations for an agreement. Follow-up can be led by the Council, or by the Conference on Disarmament if a dedicated verification review is included.",
    "china-impasse": "You are drafting in a simulated workshop. Only an initial text that already covers the wider remit is acceptable. Seek negotiations for an agreement. Follow-up can be led by the Council, or by the Conference on Disarmament if a dedicated verification review is included.",
}
CLAIMS = {
    "require_first": "The mandate explicitly makes coverage of broader issues in the first stage mandatory.",
    "forbid_first": "The mandate explicitly forbids coverage of broader issues in the first stage.",
    "require_eventual": "The mandate explicitly requires coverage of broader issues in at least one stage.",
}
SYSTEM = (
    "Test whether the given claim is an explicit constraint of the private mandate. "
    "Read the scope and its timing literally. A condition that can be met later is not mandatory now. "
    "An initial-stage obligation applies even if a subsequent phase is possible. "
    "Ignore all other requirements. Choose the answer code and respond only with that letter."
)
NOT = "The claim is not established by the mandate."
YES = "The claim is established by the mandate."


def suite():
    for panel, cards in (("original", load(CASE)["cards"]), ("reworded", RESERVE)):
        for card, mandate in cards.items():
            for key, claim in CLAIMS.items():
                for reverse in (False, True):
                    codebook = dict(zip("AB", (NOT, YES) if reverse else (YES, NOT), strict=True))
                    body = {"private_mandate": mandate, "claim": claim, "answer_codes": codebook}
                    yield {"id": f"{panel}/{card}/{key}/{int(reverse)}",
                           "entails_code": "B" if reverse else "A",
                           "messages": [{"role": "system", "content": SYSTEM},
                                        {"role": "user", "content": json.dumps(body, ensure_ascii=False)}]}


def exclude(prediction):
    first = prediction["require_first"]
    forbidden = prediction["forbid_first"]
    eventual = prediction["require_eventual"]
    if first is True and forbidden is True:
        return set(), False
    results = set()
    if first is True or eventual is True:
        results.add("focused")
    if first is True:
        results.add("staged")
    if forbidden is True:
        results.add("broad")
    return results, True


def reference(card):
    return {"require_first": card == "china-impasse", "forbid_first": card == "japan",
            "require_eventual": card != "japan"}


def score(rows):
    assert len(rows) == 36
    totals, interpretations, projections, paths = Counter(), {}, {}, {}
    for panel in ("original", "reworded"):
        scopes = {}
        for card in REFERENCE:
            prediction, decisions = {}, {}
            target = reference(card)
            assert exclude(target) == (REFERENCE[card], True)
            for k in CLAIMS:
                a, b = rows[f"{panel}/{card}/{k}/0"]["label_logits"]
                c, d = rows[f"{panel}/{card}/{k}/1"]["label_logits"]
                margins = (a - b, d - c)
                value = True if min(margins) > 0 else False if max(margins) < 0 else None
                prediction[k] = value
                decisions[k] = {"margins": margins, "value": value, "expected": target[k]}
                label = "unknown" if value is None else "correct" if value == target[k] else "wrong"
                totals[panel, "question", label] += 1
            scopes[card], consistent = exclude(prediction)
            projections[f"{panel}/{card}"] = {"rejected_scopes": sorted(scopes[card]), "consistent": consistent,
                                               "exact": scopes[card] == REFERENCE[card] and consistent}
            interpretations[f"{panel}/{card}"] = decisions
            totals[panel, "projected_sets", "exact"] += projections[f"{panel}/{card}"]["exact"]
        trace = clause_control.evaluate(scopes)["paths"]
        for key, row in trace.items():
            case = key.split("/")[0]
            totals[panel, case, row["public"]["state"]] += 1
            totals[panel, case, "slots"] += row["slots"]
            totals[panel, case, "rejected"] += sum(e.get("status") == "rejected" for e in row["events"])
            paths[f"{panel}/{key}"] = row
    return {"totals": {"/".join(k): v for k, v in totals.items()}, "questions": interpretations,
            "projections": projections, "paths": paths}


def digests():
    paths = (Path(__file__), CASE, HERE / "scope_model.py", HERE / "clause_control.py",
             HERE.parent / "decision_ledger.py", HERE / "evidence/metrics.json", ENTAILMENT / "run.py")
    return {str(p.resolve().relative_to(HERE.parents[1])): runner.digest(p) for p in paths}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("lock", "run", "replay"))
    parser.add_argument("output", type=Path, nargs="?")
    parser.add_argument("--model", type=Path)
    args = parser.parse_args()
    if args.mode == "lock":
        assert len(list(suite())) == 36
        lock = {"calls": 36, "hashes": digests(),
                "scope": "Same public routing and authored admission audit. Separate timing predicates. Reworded reserve is a paraphrase test within the same family."}
        with LOCK.open("x") as out:
            json.dump(lock, out, indent=2)
            out.write("\n")
        return
    assert load(LOCK)["hashes"] == digests()
    if args.mode == "run":
        runner.suite, runner.score = suite, score
        runner.main(args.model, args.output)
        return
    file = args.output / "predictions.jsonl"
    records = list(map(json.loads, file.read_text().splitlines()))
    assert load(args.output / "complete.json") == {"records": 36, "sha256": runner.digest(file)}
    for example, actual in zip(suite(), records, strict=True):
        assert all(actual[k] == v for k, v in example.items())
    result = score({x["id"]: x for x in records})
    assert json.loads(json.dumps(result)) == load(args.output / "metrics.json")
    print(json.dumps({"input_hashes": len(digests()), "records": 36,
                      "exact_routing_paths": len(result["paths"])}, indent=2))


if __name__ == "__main__":
    main()
