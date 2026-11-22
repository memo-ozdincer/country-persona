"""Evaluate frozen local interpretation and verification routing on a new UN case."""
import argparse
from collections import Counter
from hashlib import sha256
from itertools import product
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
RESEARCH = HERE.parents[1]
LOOKUP = HERE.parent / "disclosure/clarify/routing/partial/lookup"
ENTAILMENT = RESEARCH / "judge/entailment"
for directory in (LOOKUP, ENTAILMENT):
    sys.path.insert(0, str(directory))
import confirmation_target
import deferral
import deferral_cases
import run as judge
from package_panel import ELIGIBLE, INELIGIBLE, CONTRAST, codec

CASE = HERE / "case.json"
POLICY = LOOKUP / "evidence/deferral/policy.json"
LOCK = HERE / "preregistered.json"
CARDS = ("japan", "china-overlap", "china-impasse")
LETTERS = "ABCDEFG"
EXPECTED = {"japan": "ADF", "china-overlap": "BFG", "china-impasse": "BG"}


def load(path):
    return json.loads(path.read_text())


def truth_bits(letters):
    return sum(1 << LETTERS.index(letter) for letter in letters)


def describe(option):
    scopes = {
        "focused": "Limit the text to the existing treaty focus.",
        "staged": "Start with the existing treaty focus and explicitly assign broader issues to a second stage.",
        "broad": "Include broader issues in the first stage.",
    }
    products = {"study": "Request a study.", "negotiation": "Call for negotiations toward an agreement."}
    forums = {"council": "The Security Council leads follow-on work.",
              "disarmament": "The Conference on Disarmament leads follow-on work."}
    review = "Include a dedicated verification review." if option["review"] else "Provide no dedicated verification review."
    return " ".join((scopes[option["scope"]], products[option["instrument"]], forums[option["forum"]], review))


def authored_masks():
    options = load(CASE)["options"]
    accepted = {name: "" for name in CARDS}
    for option in options:
        label = option["id"]
        if option["scope"] in ("focused", "staged") and option["forum"] == "disarmament":
            accepted["japan"] += label
        if option["instrument"] == "negotiation" and (option["forum"] == "council" or option["review"]):
            if option["scope"] in ("staged", "broad"):
                accepted["china-overlap"] += label
            if option["scope"] == "broad":
                accepted["china-impasse"] += label
    assert accepted == EXPECTED
    return {k: truth_bits(v) for k, v in accepted.items()}


def suite():
    case = load(CASE)
    for name in CARDS:
        for option in case["options"]:
            letter = option["id"]
            source = f"Private mandate: {case['cards'][name]}\nOffered package {letter}: {describe(option)}"
            for invert in (False, True):
                ordered = (INELIGIBLE, ELIGIBLE) if invert else (ELIGIBLE, INELIGIBLE)
                yield {"id": f"{name}/{letter}/{int(invert)}", "support_code": "B" if invert else "A",
                       "messages": [{"role": "system", "content": CONTRAST},
                                    {"role": "user", "content": codec({
                                        "source": source, "highlighted_quote": source,
                                        "candidate_claims": dict(zip("AB", ordered, strict=True)),
                                    })}]}


def score(rows):
    masks = authored_masks()
    case = load(CASE)
    full = truth_bits(LETTERS)
    counts, decisions, paths = Counter(), {}, {}
    observed, margins = {}, {}
    assert set(rows) == {r["id"] for r in suite()}
    for name in CARDS:
        yes = no = 0
        margins[name] = []
        for i, letter in enumerate(LETTERS):
            a, b = rows[f"{name}/{letter}/0"]["label_logits"]
            c, d = rows[f"{name}/{letter}/1"]["label_logits"]
            pair = (a - b, d - c)
            sign = True if min(pair) > 0 else False if max(pair) < 0 else None
            expected = bool(masks[name] & (1 << i))
            decisions[f"{name}/{letter}"] = {"margins": pair, "sign": sign, "expected": expected}
            counts["local", "unknown" if sign is None else "correct" if sign == expected else "wrong"] += 1
            margins[name].append(sum(pair) / 2)
            if sign is True:
                yes |= 1 << i
            elif sign is False:
                no |= 1 << i
        observed[name] = (yes, no)
    fitted = deferral.restore(load(POLICY))
    for name in CARDS[1:]:
        truth = (masks["japan"], masks[name])
        initial = (observed["japan"], observed[name])
        exact = tuple((menu, full ^ menu) for menu in truth)
        scores = (margins["japan"], margins[name])
        target = "AGREEMENT_POSSIBLE" if name.endswith("overlap") else "IMPASSE"
        for opening in product(EXPECTED["japan"], EXPECTED[name]):
            comparisons = {}
            for arm, selected in (("mixed-script", {}), ("mixed-learned", fitted)):
                trace = deferral_cases.replay(case, opening, initial, exact, truth, selected, "authored")
                comparisons[arm] = (trace, trace["readout"]["state"], trace["events"], "slot")
            for arm, mode, limit in (("confirmation-peer", "peer", 1),
                                     ("confirmation-ranked", "score", 1),
                                     ("confirmation-two", "peer", 2)):
                trace = confirmation_target.rollout(case, opening, initial, exact, truth, scores, mode, limit)
                comparisons[arm] = (trace, trace["public"]["state"], trace["events"], "turn")
            for arm, (trace, state, events, clock) in comparisons.items():
                prefix = (name, arm)
                counts[*prefix, "correct"] += state == target
                counts[*prefix, "paths"] += 1
                counts[*prefix, "checks"] += sum("checked" in event for event in events)
                counts[*prefix, "slots"] += sum(event[clock] >= 0 for event in events)
                counts[*prefix, "rejected"] += sum(event["status"] == "untruthful" for event in events)
                paths["/".join((*prefix, "".join(opening)))] = trace
            for arm in ("mixed-script", "mixed-learned"):
                assert len(comparisons[arm][2]) <= 10
    return {"totals": {"/".join(k): v for k, v in counts.items()},
            "decisions": decisions, "paths": paths}


def hashes():
    files = (Path(__file__), CASE, POLICY, HERE / "references.json",
             LOOKUP / "deferral_cases.py", LOOKUP / "deferral.py", LOOKUP / "confirmation_target.py",
             LOOKUP / "workshop_lookup.py", LOOKUP / "lookup.py",
             ENTAILMENT / "package_panel.py", ENTAILMENT / "transfer.py", ENTAILMENT / "run.py")
    return {str(path.resolve().relative_to(RESEARCH)): sha256(path.read_bytes()).hexdigest() for path in files}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode", choices=("lock", "run", "replay"))
    p.add_argument("model", type=Path, nargs="?")
    p.add_argument("output", type=Path, nargs="?")
    args = p.parse_args()
    authored_masks()
    assert len(list(suite())) == 42
    actual = hashes()
    if args.mode == "lock":
        note = {"scope": "Local-sign and routing diagnostic on one unseen worktree family. Compare paired outcomes before totals. Exact authored check provider for every arm. Confirmation is the public scope only on overlap. Treat its impasse rows as explicit stress tests. No adaptation after outputs.",
                "source_hashes": actual, "calls": 42, "slots": 8, "continuations": 15}
        with LOCK.open("x") as out:
            out.write(json.dumps(note, indent=2) + "\n")
        return
    assert load(LOCK)["source_hashes"] == actual
    if args.mode == "run":
        assert args.model is not None and args.output is not None
        judge.suite, judge.score = suite, score
        judge.main(args.model, args.output)
        return
    destination = args.model
    predictions = destination / "predictions.jsonl"
    records = list(map(json.loads, predictions.read_text().splitlines()))
    assert load(destination / "complete.json") == {"records": 42, "sha256": judge.digest(predictions)}
    assert len(records) == 42
    for plan, record in zip(suite(), records, strict=True):
        assert all(record[k] == value for k, value in plan.items())
    result = score({r["id"]: r for r in records})
    assert json.loads(json.dumps(result)) == load(destination / "metrics.json")
    print(json.dumps({"predictions": 42, "source_hashes": len(actual),
                      "exact_routing_paths": len(result["paths"])}, indent=2))


if __name__ == "__main__":
    main()
