"""Verify peer private evidence and fault tapes cannot change the actor's observation."""
import json
import neural_router as engine


def evaluate():
    rows=engine.sp.panels((5,7),19311,80,3)
    worlds=engine.guard.messages(rows,19312,.2,.1)
    count=0
    for item in worlds:
        row,tape=item
        n,truth,local,opening,fields=row
        full=(1<<n)-1
        state=engine.sp.opened(opening,local),1,0,3
        while state[2]<n+1 and not engine.sp.terminal(state[0],full):
            _,role,_,_=state
            hidden=1-role
            possible,default=engine.candidates(item,state,engine.BASE)
            target=engine.state_features(row,state,possible,default)
            new_local=list(local)
            new_local[hidden]=(local[hidden][1],local[hidden][0])
            new_truth=list(truth)
            new_truth[hidden]=full ^ truth[hidden]
            new_fields=list(fields)
            new_fields[hidden]=0
            altered=n,tuple(new_truth),tuple(new_local),opening,tuple(new_fields)
            faults={k:(full,full) for k in tape}
            new_moves,new_default=engine.candidates((altered,faults),state,engine.BASE)
            view=engine.state_features(altered,state,new_moves,new_default)
            assert view==target and tuple(new_moves)==tuple(possible) and new_default==default
            state=engine.next_state(item,state,default,possible)
            count+=1
    return {"public_states":count,"perturbations":["peer signs","peer private truth","peer scope","future claim faults"],
            "identical_actor_view_and_legal_action_ids":True}


if __name__=="__main__":
    print(json.dumps(evaluate(),indent=2))
