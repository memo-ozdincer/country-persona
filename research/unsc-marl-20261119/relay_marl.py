"""Train a shared actor on a two-round, one-fact-per-edge UN decision relay."""
from collections import Counter
from dataclasses import dataclass
from itertools import product
import json
from pathlib import Path
import random

import torch
from torch import nn

HERE = Path(__file__).resolve().parent
KIT = HERE/"benchmark-kit"
SEED = 469571
UPDATES = 100
BATCH = 96
MESSAGE_COST = .04
PASS, OWN, FORWARD = range(3)


@dataclass(frozen=True)
class Task:
    name: str
    actions: tuple[str,...]
    first: tuple[int,...]
    second: tuple[int,...]
    labels: tuple[tuple[str,...],tuple[str,...]]

    @property
    def worlds(self):
        return tuple(product(self.first,self.second))

    @property
    def hold(self):
        return len(self.actions)-1

    def valid(self, left,right):
        return {i for i in range(self.hold) if (left&right)&(1<<i)} or {self.hold}

    def warrant(self, left,right):
        candidates = ((left,) if left else self.first,(right,) if right else self.second)
        return set.intersection(*(self.valid(a,b) for a,b in product(*candidates)))


def fixtures():
    mali=json.loads((KIT/"mali.json").read_text())
    myanmar=json.loads((KIT/"myanmar.json").read_text())
    named={
        "mali":Task(mali["family"],tuple(mali["answers"]),(1,2),(1,2),
                    tuple(tuple(s["values"]) for s in mali["signals"])),
        "myanmar":Task(myanmar["family"],tuple(myanmar["answers"]),(1,3),(2,3),
                       tuple(tuple(s["values"]) for s in myanmar["signals"])),
    }
    for f,payload in (("mali",mali),("myanmar",myanmar)):
        task=named[f]
        for (left,right), gold in zip(task.worlds,payload["gold"],strict=True):
            assert {task.actions[i] for i in task.valid(left,right)}==set(gold)
    return named


def generate(seed):
    rng=random.Random(seed)
    tasks=[]
    for size in (2,3,4):
        sets=tuple(range(1,1<<size))
        actions=(*tuple(f"package {i+1}" for i in range(size)),"hold")
        for layout in range(16):
            domains=tuple(tuple(sorted(rng.sample(sets,rng.randint(2,min(4,len(sets)))))) for _ in range(2))
            descriptions=tuple(tuple(str(bits) for bits in role) for role in domains)
            tasks.append(Task(f"menu-{size}/{layout}",actions,*domains,descriptions))
    return tasks


class Actor(nn.Module):
    def __init__(self):
        super().__init__()
        self.relay=nn.Sequential(nn.Linear(12,20),nn.Tanh(),nn.Linear(20,1))
        self.chair=nn.Sequential(nn.Linear(12,20),nn.Tanh(),nn.Linear(20,1))

    def distribution(self, kind, rows):
        score=(self.chair if kind=="chair" else self.relay)(torch.tensor(rows,dtype=torch.float32)).squeeze(-1)
        return torch.distributions.Categorical(logits=score)


def message_rows(phase, own, arrived, own_sent):
    legal=(PASS,OWN) if phase<2 or not arrived else (PASS,FORWARD) if own_sent else (PASS,OWN,FORWARD)
    if phase==2 and own_sent and not arrived:
        legal=(PASS,)
    features=[
        (1.,phase==0,phase==1,phase==2,move==PASS,move==OWN,move==FORWARD,
         bool(arrived),own_sent,own.bit_count()/6,arrived.bit_count()/6,
         bool(own&arrived))
        for move in legal
    ]
    return legal,features


def chair_rows(task,left,right):
    warranted=task.warrant(left,right)
    # This uses only public domains and the facts received by the chair.
    rows=[]
    for i in range(len(task.actions)):
        bit=(1<<i) if i!=task.hold else 0
        rows.append((1.,i==task.hold,bool(left),bool(right),bool(left&bit),bool(right&bit),
                     i in warranted, bool(left&right), left.bit_count()/task.hold,
                     right.bit_count()/task.hold, bool(any(d&bit for d in task.first)),
                     bool(any(d&bit for d in task.second))))
    return tuple(range(len(task.actions))),rows


def rollout(actor,task,world,channel="peer",greedy=False,script=False):
    first,second=world
    log_probs, entropies, delivered=[],[],[]

    def act(kind,legal,rows,choose):
        if script:
            return choose
        dist=actor.distribution(kind,rows)
        selected=dist.logits.argmax() if greedy else dist.sample()
        log_probs.append(dist.log_prob(selected))
        entropies.append(dist.entropy())
        return legal[int(selected)]

    legal,rows=message_rows(0,second,0,False)
    send=act("relay",legal,rows,OWN)
    far=second if send==OWN and channel not in ("mute_far","mute_both") else 0
    delivered.append({"round":1,"sender":"far delegate","recipient":"relay","owner":"far delegate",
                      "intended_mask":second if send==OWN else 0,"delivered_mask":far})

    legal,rows=message_rows(1,first,0,False)
    own=act("relay",legal,rows,OWN)
    near=first if own==OWN and channel not in ("mute_near","mute_both") else 0
    delivered.append({"round":1,"sender":"relay","recipient":"chair","owner":"relay",
                      "intended_mask":first if own==OWN else 0,"delivered_mask":near})

    legal,rows=message_rows(2,first,far,own==OWN)
    later=PASS if channel=="one_round" else act("relay",legal,rows,FORWARD if FORWARD in legal else PASS)
    relay_peer=far if later==FORWARD else 0
    relay_own=first if later==OWN else 0
    left=(near or relay_own) if channel not in ("mute_near","mute_both") else 0
    right=relay_peer if channel!="one_round" else 0
    if channel=="one_round":
        left=near
    intended=relay_peer or relay_own
    delivered.append({"round":2,"sender":"relay","recipient":"chair",
                      "owner":"far delegate" if later==FORWARD else "relay",
                      "intended_mask":intended,
                      "delivered_mask":intended if (right and later==FORWARD) or
                                       (left and later==OWN and channel!="one_round") else 0})

    legal,rows=chair_rows(task,left,right)
    warrant=task.warrant(left,right)
    choice=act("chair",legal,rows,min(warrant) if warrant else task.hold)
    answer=choice in task.valid(first,second)
    justified=choice in warrant
    sends=sum(bool(d["intended_mask"]) for d in delivered)
    record={"world":world,"choice":task.actions[choice],"valid":answer,"warranted":justified,
            "both_sources":bool(left and right),"messages":sends,"deliveries":delivered}
    if script:
        return record,None,None
    return record,torch.stack(log_probs).sum(),torch.stack(entropies).sum()


def cross_validate():
    sets=generate(SEED)
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    named=fixtures()
    report={}
    for reward_kind in ("outcome","warranted"):
        torch.manual_seed(SEED)
        actor=Actor()
        optimizer=torch.optim.Adam(actor.parameters(),lr=.018)
        trace=[]
        def test():
            choices={}
            with torch.no_grad():
                for name,task in named.items():
                    choices[name]={arm:[rollout(actor,task,world,channel=arm,greedy=True)[0]
                                       for world in task.worlds]
                                   for arm in ("peer","one_round","mute_far","mute_near","mute_both")}
                    choices[name]["truthful_relay"]=[rollout(actor,task,world,script=True)[0]
                                                     for world in task.worlds]
            return choices

        before=test()
        examples=random.Random(SEED+1)
        for step in range(UPDATES):
            batch=[]
            for _ in range(BATCH):
                task=examples.choice(sets)
                batch.append(rollout(actor,task,examples.choice(task.worlds)))
            rewards=torch.tensor([float(log["valid"] and (reward_kind=="outcome" or log["warranted"]))
                                  -MESSAGE_COST*log["messages"] for log,_,_ in batch])
            probs=torch.stack([p for _,p,_ in batch])
            entropy=torch.stack([e for _,_,e in batch])
            loss=-((rewards-rewards.mean())*probs+.012*entropy).mean()
            optimizer.zero_grad()
            loss.backward()
            norm=float(nn.utils.clip_grad_norm_(actor.parameters(),1.,error_if_nonfinite=True))
            optimizer.step()
            trace.append({"update":step+1,"loss":float(loss.detach()),"grad_norm":norm,
                          "reward":float(rewards.mean()),
                          **dict(Counter({k:sum(log[k] for log,_,_ in batch)
                                           for k in ("valid","warranted","both_sources","messages")}))})
        report[reward_kind]={"before":before,"after":test(),"updates":trace,
                             "weights":{k:v.tolist() for k,v in actor.state_dict().items()}}
    return {"scope":"Strictly typed private cards. A sender can pass or send an owned fact; the relay may forward only what it received in round 1. The chair sees only its delivered record and public domains. Model parameters are a trainable small CPU policy.",
            "seed":SEED,"updates":UPDATES,"batch":BATCH,"reward_message_cost":MESSAGE_COST,"arms":report}


if __name__ == "__main__":
    print(json.dumps(cross_validate(),indent=2))
