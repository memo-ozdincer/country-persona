"""One acknowledged retransmission of a verified reply, without another lookup."""
from contextlib import ExitStack
from unittest.mock import patch

import reuse_receipt as reuse

router=reuse.policy
sp=router.sp


def intended(event):
    if event.get("lookup")=="joint_fields":
        return event["qualified_acceptance"],event["qualified_exclusions"]
    if event.get("lookup")=="scope_only":
        return 0,event["scope"]
    if event["reply"] is None:
        return 0,0
    return (event["target"],0) if event["reply"] else (0,event["target"])


def enabled(choose):
    stack=ExitStack()
    stack.enter_context(reuse.singleton_enabled())
    transition=router.transition

    def step(item,state,action,options,ordinary,recorded=None):
        after,checked,event=transition(item,state,action,options,ordinary,recorded)
        if event is None:
            return after,checked,event
        row,tape=item
        width=row[0]
        public,next_role,turn,credit=after
        full=(1<<width)-1
        if turn>=width+1 or sp.terminal(public,full):
            return after,checked,event
        peer=event["respondent"]
        slot=peer*2
        yes,no=intended(event)
        yes&=~public[slot]
        no&=~public[slot+1]
        if not (yes|no):
            return after,checked,event
        assert not yes&no
        pending=sp.record(sp.record(public,peer,yes,True),peer,no,False)
        active=full&~(public[1]|public[3])
        obs=(
            sp.terminal(pending,full),bool(yes),bool(no),bool((yes|no)&event["target"]),
            active.bit_count()<=3,width+1-turn>=2,
            (yes|no).bit_count()>1,bool(event.get("cached")),event.get("lookup")=="joint_fields",
        )
        retry=choose(obs)
        if retry:
            # The verified sender retransmits only its own previously signed
            # payload. Publicly unacknowledged signatures get a new delivery
            # slot, and no lookup/query credit is restored.
            local=list(row[2])
            local[peer]=(local[peer][0]|yes,local[peer][1]|no)
            amended=(*row[:2],tuple(local),*row[3:])
            wait=router.routing.offers.WAIT
            after,_=router.guard.settle(amended,tape,(public,peer,turn,credit),wait,
                                          {wait:(yes|no,pending,next_role)},False)
            assert after[1:]==(next_role,turn+1,credit)
        target_delivered=bool((after[0][slot]|after[0][slot+1])&(yes|no)&event["target"])
        return after,checked,{**event,"admitted":event["admitted"] or target_delivered,
                              "retry_available":True,"retried":retry,
                              "retry_disclosures":sum((after[0][i]&~public[i]).bit_count()
                                                      for i in (slot,slot+1))}

    stack.enter_context(patch.object(router,"transition",new=step))
    return stack
