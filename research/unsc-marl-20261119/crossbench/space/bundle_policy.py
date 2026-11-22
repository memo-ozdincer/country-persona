"""Counterfactual routing with a truthful combined offer and exclusion."""
import argparse
from collections import Counter, defaultdict
from hashlib import sha256
import json
import os
from pathlib import Path
import socket
import subprocess
import sys

import offer_refit as refit

offers, sp = refit.offers, refit.sp
BUNDLE = 3
START = "bundle_first"
TRAIN, TEST = 72355, 932871
SCRIPTS = ("verify_first", "offer_first", "bundle_first", "bundle_open")


def available(row, current, bundle_cost):
    state, role, step, _ = current
    width, _, local, _, _ = row
    base, options = offers.moves(row, current)
    groups = sp.choices(state, local, role, step, width, 0)[1]
    positive = groups.get((0, False), groups.get((2, False)))
    negative = groups.get((3, False), groups.get((1, False)))
    if positive and negative and base[0][6] != 0 and step + bundle_cost <= width + 1:
        options[BUNDLE] = positive[0], negative[0]
    slots, open_count, unknown, _, _, _, ordinary, _ = base[0]
    obs = (tuple(options), slots <= 2, open_count <= 2, min(unknown, 2), ordinary,
           base[2], base[3], base[4], (3, False) in groups)
    return base, obs, options


def choose(base, obs, script):
    if BUNDLE in obs[0] and (script == "bundle_first" or (script == "bundle_open" and obs[7])):
        return BUNDLE
    return offers.strategy(base, "open_offer" if script == "bundle_open" else script)


def step(row, current, action, options, cost):
    if action != BUNDLE:
        return offers.transition(row, current, action, options)
    state, role, slot, credit = current
    yes, no = options[action]
    assert yes & row[1][role] and not (no & row[1][role])
    target = sp.record(sp.record(state, role, yes, True), role, no, False)
    return target, 1-role, slot+cost, credit


def rollout(row, script, table, bundle_cost=1, current=None, trace=None, events=None):
    width, private, local, opening, _ = row
    current = current or (sp.opened(opening, local), 1, 0, 3)
    full = (1 << width)-1
    calls = bundles = 0
    while current[2] < width+1 and not sp.terminal(current[0], full):
        base, obs, options = available(row, current, bundle_cost)
        action = table.get(obs, choose(base, obs, script))
        if trace is not None and len(options) > 1:
            trace.append((obs, calls, {other: step(row, current, other, options, bundle_cost)
                                       for other in options if other != action}))
        after = step(row, current, action, options, bundle_cost)
        if events is not None:
            actor, before = current[1], current[0]
            new = after[0]
            events.append({"role": actor, "slot": current[2], "action": action,
                           "accepted": new[2*actor] & ~before[2*actor],
                           "excluded": new[2*actor+1] & ~before[2*actor+1]})
        current = after
        calls += action == offers.CHECK
        bundles += action == BUNDLE
    state = current[0]
    assert all(not(state[2*r] & ~t or state[2*r+1] & t) for r,t in enumerate(private))
    return sp.terminal(state, full), current[2], calls, bundles


def measure(rows, script, table, cost=1):
    outcomes, count = [], Counter()
    for row in rows:
        out = rollout(row, script, table, cost)
        outcomes.append(out)
        tag = "agreement" if row[1][0] & row[1][1] else "impasse"
        count[tag, "paths"] += 1
        for k,v in zip(("solved","slots","checks","bundles"), out, strict=True):
            count[tag,k] += v
    return outcomes, count


def fit(cohorts):
    initial = [measure(rows, START, {})[1] for rows in cohorts]
    table, history = {}, []
    reward = sum(map(sp.fitness, initial))
    for _ in range(8):
        values, hits = defaultdict(float), Counter()
        for rows in cohorts:
            for row in rows:
                trace = []
                ok, end, checks, _ = rollout(row, START, table, trace=trace)
                for obs, prefix, alternatives in trace:
                    for action, begin in alternatives.items():
                        success, time, calls, _ = rollout(row, START, table, current=begin)
                        k = obs, action
                        values[k] += (int(success)-int(ok) + sp.COST*(end-time)
                                      + sp.CHECK_COST*(checks-prefix-calls-(action==offers.CHECK)))
                        hits[k] += 1
        candidates = sorted((-v,k) for k,v in values.items() if v>0 and hits[k]>=10)
        for _,(obs, action) in candidates:
            proposed = {**table, obs: action}
            scores = [measure(rows, START, proposed)[1] for rows in cohorts]
            if any(new[tag,"solved"] < old[tag,"solved"]
                   for old,new in zip(initial,scores,strict=True) for tag in refit.CLASSES):
                continue
            utility = sum(map(sp.fitness, scores))
            if utility <= reward:
                continue
            table,reward = proposed,utility
            history.append({"observation":obs,"action":action,"visits":hits[obs,action],
                            "scores":[sp.flatten(c) for c in scores]})
            break
        else:
            break
    return table, {"original":[sp.flatten(c) for c in initial],"updates":history}


def results(rows, table):
    learned, stats = measure(rows, START, table)
    result = {"learned":sp.flatten(stats)}
    for script,cost in (*((s,1) for s in SCRIPTS),("bundle_first",2)):
        control, metrics = measure(rows,script,{},cost)
        paired = Counter()
        for row,a,b in zip(rows,control,learned,strict=True):
            tag = "agreement" if row[1][0] & row[1][1] else "impasse"
            paired[tag,str(a[0]),str(b[0])] += 1
        result[script if cost==1 else "bundle_two_slots"] = {
            "metrics":sp.flatten(metrics),"pairs":sp.flatten(paired)}
    return result


def evaluate():
    train = sp.panels((4,5),TRAIN,350,2) + sp.panels((4,5),TRAIN+1,350,3)
    table, journal = fit((train,refit.drop_returns(train,TRAIN+2)))
    fresh = sp.panels((6,7),TEST,1000,3)
    return {"training":journal,"policy":[[k,v] for k,v in sorted(table.items())],
            "reliable":results(fresh,table),
            "missing_returns":results(refit.drop_returns(fresh,TEST+1),table)}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode",choices=("run","replay"))
    p.add_argument("directory",type=Path)
    args = p.parse_args()
    files = (Path(__file__),Path(refit.__file__),Path(offers.__file__),Path(sp.__file__),
             sp.LOOKUP/"lookup.py",sp.LOOKUP.parent/"train.py",sp.LOOKUP.parents[1]/"environment.py")
    hashes = {str(f.resolve().relative_to(sp.HERE.parents[1])):sha256(f.read_bytes()).hexdigest() for f in files}
    launch,record = args.directory/"launch.json",args.directory/"results.json"
    if args.mode == "replay":
        assert json.loads(launch.read_text())["sha256"] == hashes
        assert json.loads(json.dumps(evaluate())) == json.loads(record.read_text())
        print(json.dumps({"verified_hashes":len(hashes),"fit_and_heldout_exact":True}))
        return
    args.directory.mkdir()
    launch.write_text(json.dumps({"host":socket.gethostname(),"pid":os.getpid(),"device":"CPU","gpu_uuids":[],
                                  "process_start":subprocess.check_output(["ps","-o","lstart=","-p",str(os.getpid())],text=True).strip(),
                                  "command":[sys.executable,*sys.argv],"run_directory":str(args.directory.resolve()),
                                  "sha256":hashes},indent=2)+"\n")
    out = evaluate()
    record.write_text(json.dumps(out,indent=2)+"\n")
    print("Accepted",len(out["training"]["updates"]),"updates",flush=True)


if __name__ == "__main__":
    main()
