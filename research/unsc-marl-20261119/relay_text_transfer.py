"""Test the frozen prose-backed relay on the wider linked workshop menus."""
import argparse
from contextlib import contextmanager
from hashlib import sha256
import json
from pathlib import Path
from unittest.mock import patch

import relay_compiled_record as compiler
import relay_raw_signs as wider
import relay_text as scorer
import relay_text_context as fitted
import relay_text_train as evaluation

HERE=Path(__file__).resolve().parent
CHECKPOINT=scorer.core.KIT/"evidence/relay-text/context.json"
SHIFTS={"venezuela":3,"outer_space":2}
BASE_HASHES=scorer.hashes


def remap(mask, order):
    return sum(1<<new for new,old in enumerate(order) if mask&(1<<old))


def original():
    tasks=wider.test_families()
    return {k:tasks[k] for k in SHIFTS}


def tasks():
    result={}
    for name,task in original().items():
        shift=SHIFTS[name]
        indices=tuple(range(task.hold))
        order=indices[shift:]+indices[:shift]
        values=tuple(task.actions[i] for i in order)
        result[name]=scorer.core.Task(task.name,(*values,task.actions[-1]),
            tuple(remap(m,order) for m in task.first),tuple(remap(m,order) for m in task.second),task.labels)
        for old,new in zip(task.worlds,result[name].worlds,strict=True):
            assert {task.actions[i] for i in task.valid(*old)}=={
                result[name].actions[i] for i in result[name].valid(*new)}
    return result


def hashes():
    files=(Path(__file__), Path(wider.__file__), Path(fitted.__file__), Path(evaluation.__file__),
           wider.VENEZUELA,wider.SPACE,wider.READINGS,CHECKPOINT)
    return {**BASE_HASHES(),**{str(p.relative_to(HERE)):sha256(p.read_bytes()).hexdigest() for p in files}}


@contextmanager
def enabled():
    with patch.object(scorer,"tasks",new=tasks),patch.object(scorer,"hashes",new=hashes):
        yield


def into_original(item, rotated, canonical):
    indices=tuple(rotated.actions.index(key) for key in canonical.actions[:-1])
    def mask(value):
        return remap(value,indices)
    return [{**step,"intended_mask":mask(step["intended_mask"]),"delivered_mask":mask(step["delivered_mask"])}
            for step in item["deliveries"]]


def evaluate(directory):
    import torch
    torch.set_num_threads(1)
    locked=json.loads(CHECKPOINT.read_text())
    head=fitted.Conditional()
    head.load_state_dict({k:torch.tensor(v) for k,v in locked["parameters"].items()})
    with enabled(),torch.no_grad():
        measured=scorer.read(directory)
        transformed={}
        for label in ("base","communication_only","chair_only","both","communication_and_fixed_overlap"):
            cache={}
            for key,row in measured.items():
                _,phase,left,right,_=key
                changed=row["scores"]
                if ((phase!=3 and label in ("communication_only","both","communication_and_fixed_overlap"))
                        or (phase==3 and label in ("chair_only","both"))):
                    changed=head.logits(key,row).tolist()
                elif phase==3 and left and right and label=="communication_and_fixed_overlap":
                    changed=[v if (i!=len(changed)-1)==bool(left&right) else -10000.
                             for i,v in enumerate(changed)]
                cache[key]={**row,"scores":changed}
            transformed[label]={"greedy":evaluation.assess(cache,evaluation.Head()),
                                "expected":evaluation.expected_scores(cache,evaluation.Head())}
        domain=tasks()
    specs=compiler.load(compiler.MANIFEST)
    records={}
    for label,study in transformed.items():
        records[label]={}
        for family,task in original().items():
            records[label][family]=[]
            for world,memo in zip(task.worlds,study["greedy"][family]["peer"],strict=True):
                delivered=into_original(memo,domain[family],task)
                compiled=compiler.compile_record(task,specs[family],delivered,memo["choice"])
                assert all(not given or given==answer for given,answer in
                           zip(compiled["delivered_cards"].values(),world,strict=True))
                assert (compiled["checked_status"]!="UNRESOLVED")==memo["warranted"]
                assert compiled["word_cap"]
                records[label][family].append(compiled)
    return {"scope":"Frozen model and previously fitted relay head on two seven-option held-out fixtures, with deterministic public package rotation. Exact source compilation uses only delivered card masks. Zero new fit updates.",
            "rotation":SHIFTS,"observations":len(measured),"arms":transformed,"compiled":records}


if __name__=="__main__":
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument("mode",choices=("run","replay"))
    cli.add_argument("directory",type=Path)
    cli.add_argument("--model",type=Path)
    args=cli.parse_args()
    if args.mode=="run":
        if args.model is None:
            cli.error("--model is required for run")
        with enabled():
            scorer.score(args.model,args.directory)
    else:
        print(json.dumps(evaluate(args.directory),indent=2,ensure_ascii=False))
