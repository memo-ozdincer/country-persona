"""Read speech acts separately and require existing verified package evidence."""
import argparse
from collections import Counter
import json
from pathlib import Path

import reader
from analysis import COMMIT

HERE = Path(__file__).resolve().parent
MALI = reader.MALI / "evidence/metrics.json"
SPACE = reader.SPACE / "evidence/metrics.json"
LOCK = HERE / "factored-lock.json"
SYSTEM = (
    "Identify the named speaker's own commitments about each current package. "
    "A conditional future possibility, question, reservation, or quotation about another person "
    "does not bind the speaker's delegation. Infer nothing from the package letter. "
    "Choose the letter for exactly the commitments made in this utterance."
)


def suite():
    for row in reader.suite():
        if row["id"].split("/")[1] != "joint":
            continue
        payload = json.loads(row["messages"][1]["content"])
        del payload["private_mandate"], payload["packages"]
        yield {**row, "messages": [{"role":"system","content":SYSTEM},
                                  {"role":"user","content":json.dumps(payload,ensure_ascii=False)}]}


def score(rows):
    report, counts = {}, Counter()
    mali, space = reader.load(MALI)["package_predictions"], reader.load(SPACE)["decisions"]
    data = {x["id"]: x for x in reader.load(reader.FIXTURES)}
    for fixture, info in data.items():
        outputs = []
        for order in range(2):
            x = rows[f"{fixture}/joint/{order}"]
            top = max(x["label_logits"])
            choices = [v for v,s in zip(x["values"],x["label_logits"],strict=True) if s==top]
            outputs.append(choices[0] if len(choices)==1 else None)
        stable = outputs[0] if outputs[0]==outputs[1] else None
        speech = [None,None] if stable is None else [bool(stable & k) for k in (1,2)]
        case, family = info["card"],info["family"]
        checks = [mali[case][label]["sign"] if family=="mali" else space[f"{case}/{label}"]["sign"]
                  for label in (info["accept"],info["exclude"])]
        supported = [checks[0] is True, checks[1] is False]
        admitted = [e is True and s for e,s in zip(speech,supported,strict=True)]
        report[fixture] = {"speech":speech,"speech_reference":COMMIT[fixture],
                           "stable_package_signs":checks,
                           "decoded":{"factored":admitted},
                           "expected":info["expected"],"orders":outputs}
        counts["exact_speech"] += speech==list(COMMIT[fixture])
        counts["exact_bundle"] += admitted==info["expected"]
        for i,actual in enumerate(info["expected"]):
            counts["true_admissions"] += actual and admitted[i]
            counts["false_admissions"] += not actual and admitted[i]
            counts["withheld_true"] += actual and not admitted[i]
    return {"totals":dict(counts),"bundles":report}


def hashes():
    files = (Path(__file__),HERE/"reader.py",HERE/"analysis.py",reader.FIXTURES,SPACE,MALI,
             reader.SPACE/"study.py",reader.scope_sets.ENTAILMENT/"field_panel.py")
    return {str(p.resolve().relative_to(reader.SPACE.parents[1])):reader.runner.digest(p) for p in files}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode",choices=("lock","run","replay"))
    p.add_argument("output",type=Path,nargs="?")
    p.add_argument("--model",type=Path)
    a=p.parse_args()
    if a.mode=="lock":
        assert len(list(suite()))==16
        with LOCK.open("x") as dst:
            json.dump({"calls":16,"hashes":hashes(),"scope":"Same exposed fixtures. Read speech without the mandate. Require preexisting stable same-role package evidence before admission."},dst,indent=2)
            dst.write("\n")
        return
    assert reader.load(LOCK)["hashes"]==hashes()
    if a.mode=="run":
        reader.scope_sets.field_panel.suite,reader.scope_sets.field_panel.score=suite,score
        reader.scope_sets.field_panel.main(a.model,a.output)
        return
    path=a.output/"predictions.jsonl"
    assert reader.load(a.output/"complete.json")=={"records":16,"sha256":reader.runner.digest(path)}
    rows=list(map(json.loads,path.read_text().splitlines()))
    for item,row in zip(suite(),rows,strict=True):
        assert all(row[k]==v for k,v in item.items())
    assert json.loads(json.dumps(score({r["id"]:r for r in rows})))==reader.load(a.output/"metrics.json")
    print(json.dumps({"records":len(rows),"inputs":len(hashes()),"metrics_exact":True}))


if __name__=="__main__":
    main()
