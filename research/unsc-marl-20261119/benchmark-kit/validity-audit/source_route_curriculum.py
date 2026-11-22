"""Warm up the evidence readers under truthful qualification announcements."""
import json
from unittest.mock import patch

import numpy as np
import torch

import source_route_signal as system

WARMUP = 220
FOLLOWUP = 360
CONTEXTS_PER_MASK = 3


def train():
    rng=np.random.default_rng(system.SEED+5)
    cases=[(mask,tuple(map(int,rng.integers(2,9,size=3))))
           for mask in range(16) for _ in range(CONTEXTS_PER_MASK)]
    worlds=[system.episode(mask,weights,cap) for mask,weights in cases for cap in system.CAPS]
    a, signal_mask, b, send_mask, table=(torch.as_tensor(np.stack(values)) for values in zip(*worlds,strict=True))
    sender=torch.nn.Parameter(torch.zeros(b.shape[-1],dtype=torch.float64))
    announcer=torch.nn.Parameter(torch.tensor([3.,0.,0.,0.,0.,0.],dtype=torch.float64))
    optim=torch.optim.Adam((sender,announcer),lr=.07)
    trace=[]
    for step in range(WARMUP+FOLLOWUP):
        fixed=step<WARMUP
        if fixed:
            p=torch.stack((~signal_mask[:,:,1],signal_mask[:,:,1]),dim=-1).to(torch.float64)
        else:
            score=a@announcer
            p=torch.stack((torch.zeros_like(score),score),dim=-1).masked_fill(~signal_mask,-torch.inf).softmax(-1)
        q=(b@sender).masked_fill(~send_mask[:,:,None,None,:],-torch.inf).softmax(-1)
        paths=[]
        for i,j in system.PHASES:
            value=torch.einsum("na,nab,nb->n",q[:,0,i,j],table,q[:,1,j,i])
            paths.append(p[:,0,i]*p[:,1,j]*(value-system.SIGNAL_COST*(i+j)))
        utility=torch.stack(paths).sum(0).mean()
        optim.zero_grad()
        (-utility).backward()
        gradient=float(torch.linalg.vector_norm(sender.grad))
        assert np.isfinite(gradient)
        optim.step()
        trace.append({"step":step+1,"fixed_truthful_bits":fixed,"expected_return":float(utility.detach()),
                      "sender_gradient_norm":gradient})
    return announcer.detach().numpy(),sender.detach().numpy(),trace


def run():
    with patch.object(system,"train",new=train):
        result=system.run()
    result["training_instances"]=len(system.CAPS)*16*CONTEXTS_PER_MASK
    result["synthetic_seed"]=system.SEED+5
    result["fixed_training_steps"]=WARMUP
    result["joint_training_steps"]=FOLLOWUP
    return result


if __name__=="__main__":
    print(json.dumps(run(),indent=2))
