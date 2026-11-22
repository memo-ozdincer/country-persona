"""Learn a chair adjustment conditional on the delivered-card state."""
import json
from pathlib import Path
import sys

import torch
from torch import nn

import relay_text_train as shared


class Conditional(nn.Module):
    def __init__(self):
        super().__init__()
        self.offset=nn.Parameter(torch.zeros(4,len(shared.TYPES)))
        self.chair=nn.Parameter(torch.zeros(3,2))

    def logits(self,node,row):
        _,phase,left,right,_=node
        semantics=shared.action_types(phase,row["legal"])
        values=torch.tensor(row["scores"])+self.offset[phase,list(semantics)]
        if phase==3:
            # Public state only: no complete pair, disjoint pair, or overlapping
            # pair. The model still scores individual substantive options.
            level=0 if not (left and right) else 2 if left&right else 1
            kind=[int(semantic==4) for semantic in semantics]
            values=values+self.chair[level,kind]
        return values


def evaluate(directory):
    torch.set_num_threads(1)
    cache=shared.text.read(directory)
    worlds=shared.text.tasks()["training"]
    records=[shared.enumerate_joint_action_paths(worlds,w,cache) for w in worlds.worlds]
    nodes=sorted({node for group in records for _,trace in group for node,_ in trace})
    assert all(node[0]=="training" for node in nodes)
    targets=[
        torch.tensor([float(r["warranted"] and r["valid"])-shared.core.MESSAGE_COST*r["messages"]
                      for r,_ in group])
        for group in records
    ]
    policy=Conditional()
    optimizer=torch.optim.Adam(policy.parameters(),lr=.16)
    log=[]
    for update in range(shared.UPDATES):
        local={node:policy.logits(node,cache[node]).log_softmax(0) for node in nodes}
        team=[]
        for group,reward in zip(records,targets,strict=True):
            p=torch.stack([sum(local[node][a] for node,a in path) for _,path in group]).exp()
            assert abs(float(p.sum().detach())-1)<1e-5
            team.append(p @ reward)
        expected=torch.stack(team).mean()
        regularization=.0005*sum(x.square().mean() for x in policy.parameters())
        optimizer.zero_grad()
        (-expected+regularization).backward()
        norm=torch.linalg.vector_norm(torch.cat([x.grad.flatten() for x in policy.parameters()]))
        assert torch.isfinite(norm)
        optimizer.step()
        log.append({"update":update+1,"expected_team_return":float(expected.detach()),"gradient_norm":float(norm)})
    with torch.no_grad():
        frozen={key:{**row,"scores":policy.logits(key,row).tolist()} for key,row in cache.items()}
    return {"scope":"Freeze Qwen, train a 26-parameter action adjustment on the four synthetic worlds. No per-option correctness flag enters policy inputs. Chair conditioning uses presence and overlap of delivered cards. The two linked families remain held out.",
            "conditions":["incomplete","complete_disjoint","complete_overlap"],
            "parameters":{k:v.tolist() for k,v in policy.state_dict().items()},
            "updates":log,"expected":shared.expected_scores(frozen,shared.Head()),
            "after":shared.assess(frozen,shared.Head())}


if __name__=="__main__":
    print(json.dumps(evaluate(Path(sys.argv[1])),indent=2))
