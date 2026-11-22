"""Verify an explicit scope choice never consults the package-sign provider."""
import json
from unittest.mock import patch

import exclusive_query as engine


def evaluate():
    row=4,(1,2),((1,0),(2,0)),(1,0,2,0),(0,5)
    item=row,{(r,t):(0,0) for r in range(2) for t in range(5)}
    current=(1,0,2,0),0,0,7
    _,actions,ordinary=engine.available(item,current)
    assert engine.MATCH_SCOPE in actions and engine.policy.MATCH in actions
    with patch.object(engine.focus,"answer",side_effect=AssertionError("scope touched package oracle")):
        post,used,event=engine.transition(item,current,engine.MATCH_SCOPE,actions,ordinary)
    assert used and post[2]==2 and post[3]==1 and event["published"]==5
    assert post[0][2*event["respondent"]+1]==5 and event["reply"] is False
    direct,verified,reply=engine.transition(item,current,engine.policy.MATCH,actions,ordinary,
                                            recorded=({}, {1:False}))
    assert verified and direct[2:]==post[2:] and reply["admitted"]
    assert direct[0][2*reply["respondent"]+1]==1
    return {"scope_only_published":event["published"],"package_only_published":1,"charged_slots":2,
            "used_respondent_credit":True,"scope_did_not_call_package_oracle":True}


if __name__=="__main__":
    print(json.dumps(evaluate(),indent=2))
