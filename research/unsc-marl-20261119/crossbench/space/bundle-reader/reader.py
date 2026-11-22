"""Grounded bundle interpretation with matched atomic and joint prompts."""
import argparse
from collections import Counter
import json
from pathlib import Path
import runpy
import sys

HERE = Path(__file__).resolve().parent
SPACE = HERE.parent
MALI = SPACE.parent / "mali"
sys.path[:0] = [str(SPACE)]
import scope_sets
from scope_model import runner
space_description = runpy.run_path(str(SPACE / "study.py"))["describe"]

FIXTURES = HERE / "fixtures.json"
LOCK = HERE / "lock.json"
SYSTEM = (
    "You are the clerk in a fictional two-delegate negotiation. A claim is admissible only if the "
    "named speaker actually makes that commitment about the package as written and it is consistent "
    "with that speaker's supplied private mandate. A tentative future possibility, a question, or "
    "a report about another speaker is not a commitment. Assess each claim independently. "
    "Cite nothing in the answer. Choose the single letter for the complete set of admissible claims."
)


def load(path):
    return json.loads(path.read_text())


def description(family, package):
    if family == "space":
        return space_description(package)
    monitoring = {
        "focused": "No independent monitoring in either reporting cycle.",
        "staged": "A binding commitment for independent monitoring in the second cycle only.",
        "broad": "Independent monitoring is operational in the first reporting cycle.",
    }
    return " ".join((monitoring[package["scope"]], f"The extension is {package['term']}.",
                     f"Aggregate reporting is {package['report']}."))


def suite():
    cases = {"space": load(SPACE / "case.json"), "mali": load(MALI / "case.json")}
    for fixture in load(FIXTURES):
        case = cases[fixture["family"]]
        selected = [fixture["accept"], fixture["exclude"]]
        packages = {p["id"]: description(fixture["family"], p) for p in case["options"]
                    if p["id"] in selected}
        claims = [
            f"The speaker says the delegation can sign package {selected[0]} as written.",
            f"The speaker says the delegation cannot sign package {selected[1]} as written.",
        ]
        base = {"speaker": fixture["role"], "private_mandate": case["cards"][fixture["card"]],
                "packages": packages, "message": fixture["text"]}
        for mode, active in (("joint", (0, 1)), ("first", (0,)), ("second", (1,))):
            values = list(range(1 << len(active)))
            for order in range(2):
                ordered = values if order == 0 else list(reversed(values))
                labels = "ABCD"[:len(ordered)]
                choices = {letter: [f"claim {i+1}" for i in range(len(active)) if mask & (1 << i)]
                           for letter, mask in zip(labels, ordered, strict=True)}
                prompt = {**base, "claims": {f"claim {i+1}": claims[j] for i, j in enumerate(active)},
                          "admit_exactly": choices}
                yield {"id": f"{fixture['id']}/{mode}/{order}", "labels": labels, "values": ordered,
                       "messages": [{"role":"system","content":SYSTEM},
                                    {"role":"user","content":json.dumps(prompt,ensure_ascii=False)}]}


def score(rows):
    decoded, counts = {}, Counter()
    for row in suite():
        logits = rows[row["id"]]["label_logits"]
        candidates = [v for v, s in zip(row["values"], logits, strict=True) if s == max(logits)]
        decoded[row["id"]] = candidates[0] if len(candidates) == 1 else None
    decisions = {}
    for fixture in load(FIXTURES):
        ident = fixture["id"]
        modes = {}
        for key in ("joint","first","second"):
            answers = [decoded[f"{ident}/{key}/{i}"] for i in range(2)]
            modes[key] = answers[0] if answers[0] == answers[1] else None
        combined = modes["joint"]
        truth = fixture["expected"]
        arms = {
            "joint": [None,None] if combined is None else [bool(combined & b) for b in (1,2)],
            "split": [None if modes[k] is None else bool(modes[k]) for k in ("first","second")],
        }
        decisions[ident] = {"expected":truth,"order_stable":modes,"decoded":arms}
        for arm, outcomes in arms.items():
            counts[arm,"exact_bundle"] += outcomes == truth
            counts[arm,"any_false_admission"] += any(value is True and not actual for value,actual in zip(outcomes,truth,strict=True))
            for actual,value in zip(truth,outcomes,strict=True):
                counts[arm,"abstain" if value is None else "correct" if value==actual else "wrong"] += 1
                counts[arm,"true_admissions"] += value is True and actual
                counts[arm,"false_admissions"] += value is True and not actual
    return {"totals":{"/".join(key):n for key,n in counts.items()},"bundles":decisions}


def hashes():
    files = (Path(__file__),FIXTURES,SPACE/"case.json",MALI/"case.json",SPACE/"study.py",
             scope_sets.ENTAILMENT/"field_panel.py")
    return {str(f.resolve().relative_to(SPACE.parents[1])):runner.digest(f) for f in files}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode",choices=("lock","run","replay"))
    p.add_argument("output",type=Path,nargs="?")
    p.add_argument("--model",type=Path)
    args = p.parse_args()
    if args.mode=="lock":
        assert len(list(suite()))==48
        with LOCK.open("x") as out:
            json.dump({"calls":48,"hashes":hashes(),"scope":"Author fixtures. Model judge receives full local evidence. Paired reversed labels. Split and joint decoders use the same frozen model."},out,indent=2)
            out.write("\n")
        return
    assert load(LOCK)["hashes"]==hashes()
    if args.mode=="run":
        scope_sets.field_panel.suite,scope_sets.field_panel.score=suite,score
        scope_sets.field_panel.main(args.model,args.output)
        return
    path=args.output/"predictions.jsonl"
    assert load(args.output/"complete.json")=={"records":48,"sha256":runner.digest(path)}
    rows=list(map(json.loads,path.read_text().splitlines()))
    for example,row in zip(suite(),rows,strict=True):
        assert all(row[k]==value for k,value in example.items())
    assert json.loads(json.dumps(score({x["id"]:x for x in rows})))==load(args.output/"metrics.json")
    print(json.dumps({"records":len(rows),"hashes":len(hashes()),"bundles":8,"exact_metrics":True}))


if __name__=="__main__":
    main()
