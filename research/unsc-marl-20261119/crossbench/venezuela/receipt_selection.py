"""Select a single response from the requested set using one compiled receipt."""
import argparse
from collections import Counter
from contextlib import ExitStack
import json
from pathlib import Path
from unittest.mock import patch

import workshop_transfer as transfer

router=transfer.router
canonical=transfer.canonical
delay=transfer.episode.delay
reuse=delay.reuse
group=reuse.group
SINGLETON=reuse.singleton_enabled


def enabled(use_scope=False, choose_scope=None):
    stack=ExitStack()
    stack.enter_context(SINGLETON())
    base=router.transition
    choose=group.select

    def transition(item,state,move,actions,ordinary,recorded=None):
        if move!=group.OFFER_SET:
            return base(item,state,move,actions,ordinary,recorded)
        row,_=item
        public,actor,_,credit=state
        peer=1-actor
        yes,no=row[2][peer]
        options=actions[move]
        unknown=options&~(yes|no)
        fresh=bool(credit&(1<<peer))
        cached=bool(credit&(reuse.CACHE<<peer))
        if not unknown or options&yes or not (fresh or cached):
            return base(item,state,move,actions,ordinary,recorded)
        if recorded is not None:
            positive=sum(b for b,sign in recorded[peer].items() if unknown&b and sign is True)
        else:
            positive=unknown&row[1][peer] if row[-1][peer] else 0
        selected=choose(options,positive,options&~positive,public[2*actor])
        if selected:
            with patch.object(group,"select",new=lambda *_:selected):
                after,checked,event=base(item,state,move,actions,ordinary,recorded)
        elif use_scope and fresh:
            # This answer has the same single receipt budget. It can publish
            # a verified scope exclusion even when it cannot name a positive.
            target=choose(options,yes,no,public[2*actor])
            action=router.MATCH_SCOPE
            after,checked,event=base(item,state,action,{action:target},ordinary,recorded)
            if choose_scope is not None:
                scope=event.get("scope",0)&~public[2*peer+1]
                active=((1<<row[0])-1)&~(public[1]|public[3])
                remaining=active&~scope
                # These inputs precede delivery and describe only the signed
                # receipt, its owner's local signs, and the public frontier.
                observation=(
                    bool(scope&active), bool(scope&options), not remaining,
                    remaining.bit_count()<=2, active.bit_count()<=3,
                    bool(remaining&yes), bool(remaining&public[2*actor]),
                    bool(scope&public[2*actor]), bool(options&no),
                    bool(target), scope.bit_count()>1, row[0]-state[2]>=3,
                )
                if not choose_scope(observation):
                    after,checked,event=base(item,state,move,actions,ordinary,recorded)
            event={**event,"request_set":options}
        else:
            after,checked,event=base(item,state,move,actions,ordinary,recorded)
        if fresh and not checked:
            # A receipt read costs the same even when it does not establish
            # a unique target. Never manufacture a signature.
            after=(*after[:3],after[3]&~(1<<peer))
            checked=True
        return after,checked,{**event,"selected_after_one_receipt":True}

    stack.enter_context(patch.object(router,"transition",new=transition))
    return stack


def compare(use_scope=False):
    import local_capacity as bound

    cases=list(transfer.cases())
    results={}
    contexts=(("select_before",reuse.singleton_enabled),("select_with_receipt",enabled))
    if use_scope:
        contexts=(*contexts,("select_or_disclose_scope",lambda:enabled(True)))
    for label,context in contexts:
        totals=Counter()
        capacity=Counter()
        paths={}
        for key,item,later,labels,roles,menus,terms in cases:
            kind="agreement" if key[1]=="ru-overlap" else "impasse"
            events=[]
            with canonical.enabled(terms,"public",context):
                result=router.play(item,canonical.BASE,{},events=events,recorded=later)
                solutions=bound.routes(item,later)
            first=router.sp.opened(item[0][3],item[0][2])
            deltas=[(r,0,first[2*r]) for r in range(2) if first[2*r]]
            for e in events:
                answer=e["query"]
                if answer and answer.get("selected_after_one_receipt"):
                    assert all(role==answer["respondent"] for role,_,_ in e["disclosed"])
                    assert all(negative or bits==answer["target"] for _,negative,bits in e["disclosed"])
                deltas.extend(e["disclosed"])
            claims=[]
            for role,negative,bits in deltas:
                names=[name for i,name in enumerate(labels) if bits&(1<<i)]
                claim={"id":f"m{len(claims)+1}","role":roles[role],
                       "accepts":[] if negative else names,"excludes":names if negative else []}
                assert canonical.study.truthful_disclosure(claim,menus[role])
                claims.append(claim)
            proof=canonical.study.readout(labels,roles,claims)
            assert result[0]==(proof["state"]==("AGREEMENT_POSSIBLE" if kind=="agreement" else "IMPASSE"))
            for name,v in zip(("solved","slots","checks","queries","answers","scope"),result,strict=True):
                totals[kind,name]+=v
            capacity[kind,"reachable"]+=bool(solutions)
            capacity[kind,"presentations"]+=1
            paths["/".join(key)]={"counts":result,"events":events,"proof":proof,"claims":claims,
                                   "locally_consistent_successful_paths":len(solutions)}
        results[label]={"matched_schedule":router.sp.flatten(totals),
                        "local_path_capacity":router.sp.flatten(capacity),"paths":paths}
    return {"scope":"Author-verified source projections, one cold receipt per actor or a cached reply. The order of selecting the target and reading the respondent's receipt is the only change. Local path capacity may choose a different table per opening.",
            "case_sha256":transfer.digest(Path(__file__).with_name("case.json")),"arms":results}


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--scope",action="store_true")
    args=p.parse_args()
    print(json.dumps(compare(args.scope),indent=2))
