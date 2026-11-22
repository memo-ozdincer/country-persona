"""Train a shared action head against exact relay team returns on Qwen logits."""
import json
from pathlib import Path
import sys
from types import SimpleNamespace
from unittest.mock import patch

import torch
from torch import nn

import relay_text as text

core=text.core
UPDATES=80
TYPES=("pass","own","forward","candidate","impasse")


def action_types(phase,legal):
    if phase!=3:
        return tuple(legal)
    return tuple(4 if i==len(legal)-1 else 3 for i in legal)


class Head(nn.Module):
    def __init__(self):
        super().__init__()
        self.offset=nn.Parameter(torch.zeros(4,len(TYPES)))

    def forward(self,base,semantic,phase):
        return base+self.offset[phase,list(semantic)]


class NeedChoice(Exception):
    def __init__(self,size):
        self.size=size


class Adapter:
    def __init__(self,name,cache,head,forced=None,truthful_messages=False,checked_chair=False):
        self.name=name
        self.cache=cache
        self.head=head
        self.forced=forced
        self.trace=[]
        self.truthful_messages=truthful_messages
        self.checked_chair=checked_chair

    def distribution(self,kind,rows):
        phase, a,b,sent,legal=self.view
        key=(self.name,phase,a,b,sent)
        if self.forced is not None:
            position=len(self.trace)
            if len(legal)>1 and position>=len(self.forced):
                raise NeedChoice(len(legal))
            if len(legal)>1:
                chosen=self.forced[position]
                self.trace.append((key,chosen))
            else:
                chosen=0
            return SimpleNamespace(sample=lambda:torch.tensor(chosen),
                                   log_prob=lambda _:torch.tensor(0.),
                                   entropy=lambda:torch.tensor(0.))
        if len(legal)==1:
            return torch.distributions.Categorical(logits=torch.zeros(1))
        stored=self.cache[key]
        assert list(legal)==stored["legal"]
        logits=torch.tensor(stored["scores"],dtype=torch.float32)
        if self.truthful_messages and phase!=3:
            prefer=core.FORWARD if core.FORWARD in legal else core.OWN
            scores=torch.zeros_like(logits)
            scores[legal.index(prefer)]=1.
        elif self.checked_chair and phase==3:
            warrant=self.task.warrant(a,b)
            prefer=min(warrant) if warrant else self.task.hold
            scores=torch.zeros_like(logits)
            scores[legal.index(prefer)]=1.
        else:
            scores=self.head(logits,action_types(phase,legal),phase)
        self.trace.append({"phase":phase,"observation":key,"actions":legal,"base":logits.tolist(),
                           "applied":scores.tolist()})
        return torch.distributions.Categorical(logits=scores)

    def play(self,task,world,channel="peer"):
        self.task=task
        message, chair=core.message_rows,core.chair_rows

        def observe_message(phase,own,arrived,sent):
            legal,rows=message(phase,own,arrived,sent)
            self.view=phase,own,arrived,sent,legal
            return legal,rows

        def observe_chair(task,left,right):
            legal,rows=chair(task,left,right)
            self.view=3,left,right,False,legal
            return legal,rows

        with patch.object(core,"message_rows",new=observe_message),patch.object(core,"chair_rows",new=observe_chair):
            record,_,_=core.rollout(self,task,world,channel=channel,greedy=self.forced is None)
        return record,self.trace


def enumerate_joint_action_paths(task,world,cache,name="training"):
    def expand(prefix):
        actor=Adapter(name,cache,None,forced=prefix)
        try:
            record,choices=actor.play(task,world)
        except NeedChoice as missing:
            for i in range(missing.size):
                yield from expand((*prefix,i))
            return
        assert len(choices)==len(prefix)
        yield record,tuple(choices)

    return tuple(expand(()))


def assess(cache,head):
    observations=text.tasks()
    reports={}
    with torch.no_grad():
        for name,task in observations.items():
            reports[name]={}
            for arm in ("peer","one_round","mute_far","mute_near","mute_both",
                        "full_relay_qwen_chair","qwen_relay_checked_chair"):
                reports[name][arm]=[]
                for world in task.worlds:
                    active=Adapter(name,cache,head,truthful_messages=arm=="full_relay_qwen_chair",
                                   checked_chair=arm=="qwen_relay_checked_chair")
                    channel=(arm if arm in ("one_round","mute_far","mute_near","mute_both") else "peer")
                    record,trace=active.play(task,world,channel)
                    reports[name][arm].append({**record,"decisions":trace})
    return reports


def expected_scores(cache,head):
    aggregate={}
    with torch.no_grad():
        for name,task in text.tasks().items():
            measures=[]
            for world in task.worlds:
                total={k:0. for k in ("valid","warranted","both_sources","messages")}
                mass=0.
                for record,tail in enumerate_joint_action_paths(task,world,cache,name):
                    log_prob=0.
                    for key,index in tail:
                        row=cache[key]
                        probs=head(torch.tensor(row["scores"]),action_types(key[1],row["legal"]),key[1]).log_softmax(0)
                        log_prob+=float(probs[index])
                    prob=torch.tensor(log_prob).exp().item()
                    mass+=prob
                    for key in total:
                        total[key]+=prob*record[key]
                assert abs(mass-1)<1e-5
                measures.append(total)
            aggregate[name]={k:sum(m[k] for m in measures)/len(measures) for k in measures[0]}
    return aggregate


def fit(cache,outcome_kind):
    task=text.tasks()["training"]
    paths=tuple(enumerate_joint_action_paths(task,world,cache) for world in task.worlds)
    nodes={key for episode in paths for _, trace in episode for key,_ in trace}
    assert all(key[0]=="training" for key in nodes)
    head=Head()
    optimizer=torch.optim.Adam(head.parameters(),lr=.16)
    updates=[]
    for step in range(UPDATES):
        cached={}
        for node in sorted(nodes):
            row=cache[node]
            phase=node[1]
            scores=head(torch.tensor(row["scores"]),action_types(phase,row["legal"]),phase)
            cached[node]=scores.log_softmax(0)
        world_rewards=[]
        for branches in paths:
            logs=torch.stack([sum(cached[node][action] for node,action in trace)
                              for _,trace in branches])
            prob=logs.exp()
            assert abs(float(prob.sum().detach())-1)<1e-5
            final=torch.tensor([float(record["valid"] and
                    (outcome_kind=="outcome" or record["warranted"]))-core.MESSAGE_COST*record["messages"]
                                for record,_ in branches])
            world_rewards.append(prob @ final)
        expected=torch.stack(world_rewards).mean()
        loss=-expected+0.0005*head.offset.square().mean()
        optimizer.zero_grad()
        loss.backward()
        grad=float(head.offset.grad.norm())
        assert torch.isfinite(head.offset.grad).all()
        optimizer.step()
        updates.append({"update":step+1,"expected_team_return":float(expected.detach()),
                        "gradient_norm":grad})
    return {"head":head.offset.detach().tolist(),"updates":updates,
            "terminal_rollouts_per_world":[len(x) for x in paths],"observations_optimized":len(nodes),
            "after":assess(cache,head),"expected":expected_scores(cache,head)}


def run(directory):
    torch.set_num_threads(1)
    cache=text.read(directory)
    return {"scope":"Exact expected-return training of a shared 4 x 5 action-logit head. Frozen Qwen scores every local prose observation. Only worlds from the synthetic archive review enter the optimizer. Two named UN-linked fixtures are evaluation only.",
            "base":assess(cache,Head()),"base_expected":expected_scores(cache,Head()),
            "arms":{arm:fit(cache,arm) for arm in ("outcome","warranted")}}


if __name__=="__main__":
    print(json.dumps(run(Path(sys.argv[1])),indent=2))
