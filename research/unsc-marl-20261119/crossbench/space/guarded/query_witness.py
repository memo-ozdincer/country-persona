"""Same requester observation, three different authorized peer responses."""
import json

import query_peer as engine


def evaluate():
    receipts={}
    original=None
    for tag,truth,evidence in (("positive",3,(3,0)),("negative",2,(2,1)),("unknown",3,(2,0))):
        row=4,(1,truth),((1,0),evidence),(1,0,2,0),(0,0)
        item=(row,{(r,t):(0,0) for r in range(2) for t in range(5)})
        before=(1,0,2,0),0,0,7
        obs,legal,normal=engine.choices(item,before)
        signature=obs,legal
        if original is None:
            original=signature
        assert signature==original and engine.MATCH in legal
        after,checked,event=engine.advance(item,before,engine.MATCH,legal,normal)
        assert after[2]==2 and not checked and after[3]==3
        receipts[tag]={"before":before[0],"after":after[0],"receipt":event,
                       "certified":engine.sp.terminal(after[0],15)}
    assert [r["receipt"]["reply"] for r in receipts.values()] == [True,False,None]
    assert [r["certified"] for r in receipts.values()] == [True,False,False]
    row=4,(1,2),((1,2),(2,13)),(1,0,2,0),(0,0)
    item=(row,{(r,t):(0,0) for r in range(2) for t in range(5)})
    before=(1,2,2,9),0,1,7
    obs,legal,normal=engine.choices(item,before)
    after,checked,response=engine.advance(item,before,engine.HOLE,legal,normal)
    assert not checked and after[2]==3 and engine.sp.terminal(after[0],15)
    return {"scope":"Isolated public-state test. Same requester signs, public record, credit and legal query for three peer states.",
            "identical_pre_query_signature":True,"match":receipts,
            "single_remaining_impasse_package":{"receipt":response,"after":after[0],"certified":True}}


if __name__=="__main__":
    print(json.dumps(evaluate(),indent=2))
