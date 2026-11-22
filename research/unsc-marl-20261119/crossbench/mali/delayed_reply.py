"""Let an ordinary exchange occur before resending an acknowledged reply."""
from contextlib import ExitStack
from unittest.mock import patch

import retry_reply as immediate

router,sp=immediate.router,immediate.sp
reuse=immediate.reuse
WAIT=router.routing.offers.WAIT
CHECK=router.routing.offers.CHECK


def authorized_retry(item,state,peer,yes,no):
    row,tape=item
    public,next_role,slot,credit=state
    index=2*peer
    assert not yes&no
    local=list(row[2])
    local[peer]=(local[peer][0]|yes,local[peer][1]|no)
    amended=(*row[:2],tuple(local),*row[3:])
    target=sp.record(sp.record(public,peer,yes,True),peer,no,False)
    after,_=router.guard.settle(amended,tape,(public,peer,slot,credit),WAIT,
                               {WAIT:(yes|no,target,next_role)},False)
    assert after[1:]==(next_role,slot+1,credit)
    assert all(not (new&~old) for i,(old,new) in enumerate(zip(public,after[0],strict=True))
               if i//2!=peer)
    delivered=tuple(after[0][i]&~public[i] for i in (index,index+1))
    return after,delivered


def enabled(choose):
    stack=ExitStack()
    stack.enter_context(reuse.singleton_enabled())
    available,transition=router.available,router.transition
    previous={0:None,1:None}

    def step(item,state,action,options,ordinary,recorded=None):
        after,checked,event=transition(item,state,action,options,ordinary,recorded)
        if event is None:
            actor=state[1]
            # A sender can compare its last ordinary signed payload with its
            # public acknowledgement. It cannot inspect another role's history.
            if action==reuse.ROUTER.ROUTINE and ordinary[0]!=CHECK:
                planned=router.routing.step(item[0],state,*ordinary,1)[0]
                owned=(2*actor,2*actor+1)
                sent=tuple(planned[i]&~state[0][i] for i in owned)
                if any(sent):
                    previous[actor]=(sent[0]&~after[0][owned[0]])|(sent[1]&~after[0][owned[1]])
            return after,checked,event
        public,next_role,slot,credit=after
        width=item[0][0]
        full=(1<<width)-1
        if slot>=width+1 or sp.terminal(public,full):
            return after,checked,event
        sender=event["respondent"]
        index=2*sender
        yes,no=immediate.intended(event)
        yes&=~public[index]
        no&=~public[index+1]
        if not (yes|no):
            return after,checked,event
        complete=sp.record(sp.record(public,sender,yes,True),sender,no,False)
        active=full&~(public[1]|public[3])
        slots=width+1-slot
        obs=(sp.terminal(complete,full),bool(yes),bool(no),bool((yes|no)&event["target"]),
             active.bit_count()<=3,slots>=2,(yes|no).bit_count()>1,
             bool(event.get("cached")),event.get("lookup")=="joint_fields",slots>=3,
             previous[sender] is not None,bool(previous[sender]),
             bool((previous[sender] or 0)&(yes|no)))
        picked=choose(obs)
        if picked=="delayed" and slots<2:
            picked="immediate"
        event={**event,"retry_action":picked,"retry_opportunity":True}
        if picked=="continue":
            return after,checked,event
        if picked=="delayed":
            _,moves,regular=available(item,after)
            move,regular_options=regular
            # One ordinary public action precedes the resend. If the ordinary
            # scheduler would verify a source, use its already-legal WAIT.
            next_action=(WAIT if move==CHECK else move),regular_options
            current=after
            after,new_check,other=transition(item,current,reuse.ROUTER.ROUTINE,moves,next_action,recorded)
            assert not new_check and other is None and after[2:]==(slot+1,credit)
            assert all(not (new&~old) for i,(old,new) in enumerate(zip(public,after[0],strict=True))
                       if i//2!=next_role)
            event.update(handoff_slot=slot,handoff_role=next_role,
                         handoff_signs=sum((new&~old).bit_count()
                                           for old,new in zip(public,after[0],strict=True)))
            if sp.terminal(after[0],full):
                return after,checked,{**event,"retry_cancelled_terminal":True}
        before_retry=after
        retained=before_retry[0]
        retry_yes=yes&~retained[index]
        retry_no=no&~retained[index+1]
        if not (retry_yes|retry_no):
            return after,checked,event
        after,delivered=authorized_retry(item,before_retry,sender,retry_yes,retry_no)
        return after,checked,{**event,"retry_slot":before_retry[2],
                              "admitted":event["admitted"] or bool((delivered[0]|delivered[1])&event["target"]),
                              "retry_signs":sum(n.bit_count() for n in delivered)}

    stack.enter_context(patch.object(router,"transition",new=step))
    return stack
