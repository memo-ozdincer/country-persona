"""Evaluate local deferral and follow-up rules together under the team reward."""
import argparse
from collections import defaultdict
from itertools import product
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
from unittest.mock import patch

import general_rules as original

HERE=Path(__file__).resolve().parent
study,prior,sp=original.study,original.prior,original.sp


def proposals(ranked):
    actions=defaultdict(list)
    for rule in ranked:
        actions[rule[0]].append(rule)
    # Preserve coverage for each legal action in the proposal set.
    single=[(rule,) for candidates in actions.values() for rule in candidates[:5]]
    defer=actions[original.DEFER][:5]
    query=[r for r in ranked if r[0] not in (original.DEFER,original.policy.policy.ROUTINE)][:8]
    return [*single,*product(defer,query)]


def summaries(sets,rules):
    return tuple(original.count(rows,rules)[1] for rows in sets)


def qualifies(old,new):
    return all(b[class_,"solved"]>=a[class_,"solved"]
               for a,b in zip(old,new,strict=True) for class_ in original.CLASSES)


def learn(training,development,teacher):
    rules=()
    anchors=tuple(summaries(rows,rules) for rows in (training,development))
    current=sum(map(prior.quality,anchors[0])),sum(map(prior.quality,anchors[1]))
    journal=[]
    for _ in range(5):
        ranked,potential=original.rank(training,teacher,rules)
        tests=[]
        best=None
        for edit in proposals(ranked):
            update=(*rules,*edit)
            before=summaries(training,update)
            score=sum(map(prior.quality,before))
            row={"edits":edit,"potential":[potential[r] for r in edit],"train_gain":score-current[0]}
            if score>current[0] and qualifies(anchors[0],before):
                dev=summaries(development,update)
                val=sum(map(prior.quality,dev))
                passed=val>=current[1] and qualifies(anchors[1],dev)
                row.update(validation_gain=val-current[1],passed=passed)
                if passed and (best is None or (score,val)>best[0]):
                    best=(score,val),update,before,dev,edit
            tests.append(row)
        iteration={"candidates":tests}
        journal.append(iteration)
        if best is None:
            break
        current,rules,before,dev,edit=best
        iteration.update(accepted=edit,train=[sp.flatten(x) for x in before],
                         validation=[sp.flatten(x) for x in dev])
    return rules,journal


def compute(metrics,table_archive):
    with patch.object(original,"learn",new=learn):
        return original.test(metrics,table_archive)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode",choices=("run","replay"))
    p.add_argument("directory",type=Path)
    p.add_argument("metrics",type=Path)
    args=p.parse_args()
    archive=HERE/"evidence/trajectory-fit/results.json"
    prior_lock=HERE/"evidence/general-rules/launch.json"
    hashes=study.mali.load(prior_lock)["sha256"]
    base_hashes=study.mali.load(HERE/"evidence/trajectory-fit/launch.json")["sha256"]
    assert base_hashes=={**study.hashes(),"deferral":prior.digest(Path(prior.defer.__file__)),
                         "trajectory":prior.digest(Path(prior.__file__)),
                         "mali_receipts":prior.digest(args.metrics),
                         "stepwise":prior.digest(HERE/"evidence/joint-transfer/defer-fit.json")}
    assert hashes=={**base_hashes,"rules":prior.digest(Path(original.__file__)),
                    "prior_results":prior.digest(archive)}
    hashes.update(paired_rules=prior.digest(Path(__file__)))
    launch=args.directory/"launch.json"
    result=args.directory/"results.json"
    source=study.mali.load(args.metrics)
    controls=study.mali.load(archive)
    if args.mode=="replay":
        assert study.mali.load(launch)["sha256"]==hashes
        assert json.loads(json.dumps(compute(source,controls)))==study.mali.load(result)
        print(json.dumps({"exact":True,"hashes":len(hashes)}))
        return
    args.directory.mkdir()
    identity={"host":socket.gethostname(),"pid":os.getpid(),"device":"CPU","gpu_uuids":[],
              "process_start":subprocess.check_output(["ps","-o","lstart=","-p",str(os.getpid())],text=True).strip(),
              "command":[sys.executable,*sys.argv],"run_directory":str(args.directory.resolve()),"sha256":hashes}
    launch.write_text(json.dumps(identity,indent=2)+"\n")
    data=compute(source,controls)
    result.write_text(json.dumps(data,indent=2)+"\n")
    print({"accepted_rules":len(data["rules"])},flush=True)


if __name__=="__main__":
    main()
