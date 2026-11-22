"""Select shared packet and handoff policies against the same team reward."""
from collections import Counter
from itertools import product
import json
from unittest.mock import patch

import numpy as np

import delivery_handoff as floor
import same_polarity_repair as packet

fit, core, router = packet.fit, packet.prior, packet.router
SEEDS = {"train": 623379, "dev": 281609, "heldout": 579311, "archive": 766031}
OPTIONS = tuple(product((False,True),repeat=2))
FEATURES = {"packet":packet.FEATURES, "handoff":floor.FEATURES}
CLASSES = ("agreement","impasse")
FIXED = (None,None)


def play(item, terms, receipt, send_extra, handoff, events=None):
    pending = [(0,0), (0,0)]
    seen_loss = [False,False]
    views = [None,None]
    chronology = []
    full = (1<<item[0][0])-1
    with fit.protocol(terms):
        base = router.transition

        def step(row,state,action,choices,routine,recorded=None):
            if action!=core.ROUTINE:
                return base(row,state,action,choices,routine,recorded)
            normal = core.intended(state,routine)
            if not any(normal):
                return base(row,state,action,choices,routine,recorded)
            public, role, slot, credit = state
            peer, index = 1-role,2*role
            payload = normal
            extra = False
            if views[0] is None and (normal[0]|normal[1]).bit_count()==1:
                _, candidate = packet.select(row,terms,state,normal,pending[role])
                if candidate is not None:
                    joined, detail = candidate
                    frame, coded, ordinary, _, _ = routine
                    _, following, end, left = router.routing.step(frame[0],coded,*ordinary,1)
                    assert end==slot+1 and left==credit
                    views[0] = (*detail[:-1],following==role,detail[-1])
                    extra = send_extra(views[0])
                    chronology.append(("packet",slot,role,extra))
                    if extra:
                        payload = joined
            if extra:
                assert (payload[0]|payload[1]).bit_count()==2
                assert not (payload[0]&~row[0][1][role] or payload[1]&row[0][1][role])
                after,_=fit.episode.delay.authorized_retry(
                    row,(public,following,slot,credit),role,*payload)
                checked,event=False,None
            else:
                after,checked,event=base(row,state,action,choices,routine,recorded)
            ledger,next_role,finish,remaining = after
            yes,no = payload[0]&~ledger[index],payload[1]&~ledger[index+1]
            pending[role] = yes,no
            if not (yes|no):
                return after,checked,event
            if (views[1] is None and next_role==role and finish<row[0][0]+1
                    and not router.sp.terminal(ledger,full)):
                live=full & ~(ledger[1]|ledger[3])
                views[1] = (payload==(yes,no),bool(yes),bool(no),(yes|no).bit_count()>1,
                    bool(yes&ledger[2*peer]),bool(live&ledger[2*role]),bool(live&ledger[2*peer]),
                    live.bit_count()<=3,bool(remaining&(1<<peer)),bool(remaining&(1<<role)),
                    bool(remaining&fit.selection.reuse.ROUTER.CREDIT),row[0][0]+1-finish>=4,
                    seen_loss[role])
                transfer = handoff(views[1])
                chronology.append(("handoff",slot,role,transfer))
                if transfer:
                    after = ledger,peer,finish,remaining
            seen_loss[role] = True
            return after,checked,event

        with patch.object(router,"transition",new=step):
            result=router.play(item,fit.BASE,{},events=events,recorded=receipt)
    return result,views,chronology


def cases(rows):
    for item,terms,receipt in rows:
        paths = [play(item,terms,receipt,lambda _:a,lambda _:b) for a,b in OPTIONS]
        yield fit.world_label(item),paths


def candidates(names):
    return (None,(),*((i,v) for i in range(len(names)) for v in (False,True)))


def match(rule, view):
    return view is not None and rule is not None and (not rule or view[rule[0]]==rule[1])


def exact(paths, rulepair):
    ordered = [r for (actions,r) in zip(OPTIONS,paths,strict=True)
               if all(view is None or choice==match(rule,view)
                      for choice,rule,view in zip(actions,rulepair,r[1],strict=True))]
    assert ordered and all(r==ordered[0] for r in ordered)
    return ordered[0]


def make_grid():
    return tuple(product(*(candidates(features) for features in FEATURES.values())))


def count_grid(panels, grid):
    shaped={}
    for regime,rows in panels.items():
        for label in CLASSES:
            stats=np.zeros((len(grid),3),dtype=np.int64)
            # Most episodes have no legal intervention. Aggregate identical
            # branch trees before evaluating the two local decision rules.
            groups=Counter(tuple((tuple(outcome[:3]),tuple(views),tuple(chronology))
                                 for outcome,views,chronology in paths)
                           for kind,paths in rows if kind==label)
            for paths, weight in groups.items():
                if all(v is None for v in paths[0][1]):
                    stats += weight*np.asarray(paths[0][0])
                    continue
                stats += weight*np.asarray([exact(paths,rule)[0] for rule in grid])
            shaped[regime,label] = stats
    return shaped


def optimize(train,dev):
    grid=make_grid()
    assert grid[0]==FIXED
    t,v=count_grid(train,grid),count_grid(dev,grid)

    def assess(allowed):
        accepted=[]
        for i, pair in enumerate(grid):
            if not allowed(pair):
                continue
            gains = {"train": {}, "dev": {}}
            for label,split in (("train",t),("dev",v)):
                for key,values in split.items():
                    gains[label]["/".join(key)] = (values[i]-values[0]).tolist()
            if min(c[0] for data in gains.values() for c in data.values()) < 0:
                continue
            rewards={k:sum(int(np.dot(c,[200,-3,-1])) for c in by.values()) for k,by in gains.items()}
            complexity=sum(rule is not None for rule in pair)
            accepted.append(((rewards["dev"],rewards["train"],-complexity,-i),pair,gains))
        best=max(accepted,key=lambda r:r[0])
        return {"rules":best[1],"rewards":best[0][:2],"deltas":best[2],"candidates":len(accepted)}

    fit_packet=assess(lambda rules: rules[1] is None)
    fit_handoff=assess(lambda rules: rules[0] is None)
    joint=assess(lambda _:True)
    return {"packet_only":fit_packet,"handoff_only":fit_handoff,"joint":joint,
            "separate_pair":{"rules":(fit_packet["rules"][0],fit_handoff["rules"][1])}}


def report(panels, selected):
    controls={"fixed":FIXED,"always_packet":((),None),"always_handoff":(None,()),
              "always_both":((),()),**{name:rule["rules"] for name,rule in selected.items()}}
    total={}
    for regime,rows in panels.items():
        result={}
        headroom=Counter()
        for kind,paths in rows:
            ever={record[0] for _,_,events in paths for record in events}
            if len(ever)==2:
                headroom[kind,"both_legal_in_some_branch"]+=1
                u=[200*int(x[0])-3*x[1]-x[2] for x,_,_ in paths]
                if u[3]-u[2]-u[1]+u[0]:
                    headroom[kind,"nonadditive_return"]+=1
                if paths[3][0][0] and not any(p[0][0] for p in paths[:3]):
                    headroom[kind,"certificate_needs_both"]+=1
        for name,policy in controls.items():
            counts,pairs=Counter(),Counter()
            for kind,paths in rows:
                value,views,chronology=exact(paths,policy)
                pairs[kind,str(paths[0][0][0]),str(value[0])] += 1
                counts[kind,"presentations"]+=1
                for key,x in zip(("certificate","slots","checks","queries","answers","scope"),value,strict=True):
                    counts[kind,key]+=x
                for stage,_,_,active in chronology:
                    counts[kind,f"{stage}_decisions"]+=1
                    counts[kind,f"{stage}_actions"]+=active
            result[name]={"counts":router.sp.flatten(counts),"paired":router.sp.flatten(pairs)}
        total[regime]={"support":router.sp.flatten(headroom),"arms":result}
    return total


def run():
    with patch.object(fit,"SEEDS",new=SEEDS):
        train={k:list(cases(v)) for k,v in fit.synth("train",(5,6),650,2).items()}
        dev={k:list(cases(v)) for k,v in fit.synth("dev",(6,),550,3).items()}
        selected=optimize(train,dev)
        test={k:list(cases(v)) for k,v in fit.synth("heldout",(7,8),450,3).items()}
        linked={f:{k:list(cases(v)) for k,v in p.items()} for f,p in core.audit.samples()
                if f!="fresh_synthetic"}
    return {"scope":"Train two shared decentralized decision rules on exact paired synthetic team returns. Both choices available once. Each branch retains actual delivery and legal action boundaries. UN workshops are held out from all selection.",
            "seeds":SEEDS,"features":FEATURES,"fit":selected,
            "development":report(dev,selected),"heldout":report(test,selected),
            "workshops":{name:report(p,selected) for name,p in linked.items()}}


if __name__ == "__main__":
    print(json.dumps(run(),indent=2))
