"""Learn and audit a paid availability announcement before evidence delivery."""
from hashlib import sha256
from itertools import product
import json
from pathlib import Path

import numpy as np
import torch

import source_route_fit as base

SEED = 91031
UPDATES = 180
SIGNAL_COST = .05
BITS = (0, 1)
CAPS = tuple(product(range(4), repeat=2))
PHASES = tuple(product(BITS, repeat=2))
POLICIES = np.array(list(product((0,), (0,1), (0,2), (0,1,2))))
ANNOUNCEMENTS = tuple(product((0,), (0,), BITS, BITS))


def episode(public, weights, caps):
    availability = (caps[0], caps[1] << 2)
    common, legal, table = base.problem(public, weights, availability)
    signal_x, signal_legal, send_x = [], [], []
    for seat in range(2):
        own_qual = base.CHOICES[seat][2]
        peer_qual = base.CHOICES[1-seat][2]
        missing = (float(not public & own_qual), float(not public & peer_qual))
        known_positions = ((public & 1 != 0) + (public & 4 != 0)) / 2
        signal_x.append([1., *missing, known_positions, weights[2]/7,
                         float(caps[seat] == 3)])
        signal_legal.append([True, bool(availability[seat] & own_qual)])
        condition = []
        for own, peer in PHASES:
            additions = [[float(a == 0 and bool(peer)),
                          float(a == 2 and bool(peer)),
                          float(a == 2 and not peer),
                          float(a == 2 and bool(own)),
                          float(a == 1 and bool(peer))] for a in range(3)]
            condition.append(np.concatenate((common[seat], additions), axis=1))
        send_x.append(np.stack(condition).reshape(2,2,3,-1))
    return np.array(signal_x), np.array(signal_legal), np.stack(send_x), legal, table


def train():
    rng = np.random.default_rng(SEED)
    train_cases = [(int(rng.integers(16)), tuple(map(int,rng.integers(2,9,size=3))),
                    tuple(map(int,rng.integers(4,size=2)))) for _ in range(224)]
    arrays = tuple(np.stack(x) for x in zip(*(episode(*x) for x in train_cases), strict=True))
    a, signal_mask, b, send_mask, gains = (torch.as_tensor(x) for x in arrays)
    signal = torch.nn.Parameter(torch.zeros(a.shape[-1], dtype=torch.float64))
    send = torch.nn.Parameter(torch.zeros(b.shape[-1], dtype=torch.float64))
    optim = torch.optim.Adam((signal,send),lr=.07)
    traces=[]
    for t in range(UPDATES):
        x = a @ signal
        p = torch.stack((torch.zeros_like(x),x),dim=-1).masked_fill(~signal_mask,-torch.inf).softmax(-1)
        q = (b @ send).masked_fill(~send_mask[:,:,None,None,:],-torch.inf).softmax(-1)
        payoffs=[]
        for i,j in PHASES:
            given = torch.einsum("na,nab,nb->n",q[:,0,i,j],gains,q[:,1,j,i])
            payoffs.append(p[:,0,i]*p[:,1,j]*(given-SIGNAL_COST*(i+j)))
        utility=torch.stack(payoffs).sum(0).mean()
        optim.zero_grad()
        (-utility).backward()
        gradient=float(torch.linalg.vector_norm(torch.cat([signal.grad,send.grad])))
        assert np.isfinite(gradient)
        optim.step()
        traces.append({"step":t+1,"expected_return":float(utility.detach()),"gradient_norm":gradient})
    return signal.detach().numpy(),send.detach().numpy(),traces


def terminal_matrix(public,weights):
    return np.array([[base.reward(public | a | b,weights)-base.MESSAGE_COST*(bool(a)+bool(b))
                      for b in base.CHOICES[1]] for a in base.CHOICES[0]])


def optimize(public,weights):
    # Exact decentralized optimization for uniform independent four-cap priors.
    # Queries from each sender reveal only their legal positive bit or silence.
    table=terminal_matrix(public,weights)
    possible=table[POLICIES[:,None,:,None],POLICIES[None,:,None,:]]
    no_signal=possible.mean(axis=(2,3)).max()
    best=-np.inf
    fixed=-np.inf
    for left,right in product(ANNOUNCEMENTS,repeat=2):
        scores=0.
        for x,y in PHASES:
            cap_pair = (np.equal(left,x)[:,None] & np.equal(right,y)[None,:])
            scores += (possible*cap_pair).sum(axis=(2,3)).max()/len(CAPS)
        scores -= SIGNAL_COST*(sum(left)+sum(right))/4
        best=max(best,scores)
        if (left,right)==(ANNOUNCEMENTS[-1],ANNOUNCEMENTS[-1]):
            fixed=scores
    return tuple(map(float,(no_signal, fixed, best)))


def inspect(public,weights,caps,w_signal,w_send):
    signal_features, allowed, block_features, legal, gain=episode(public,weights,caps)
    chosen=tuple(int(x) for x in np.where(allowed[:,1],signal_features@w_signal,-np.inf)>0)
    left,right=chosen
    vectors=np.stack((block_features[0,left,right],block_features[1,right,left]))
    decisions=np.where(legal,vectors@w_send,-np.inf).argmax(axis=1)
    proof=base.reward(public|base.CHOICES[0][decisions[0]]|base.CHOICES[1][decisions[1]],weights)
    return {"private":caps,"signals":chosen,"blocks":tuple(int(x) for x in decisions),"proof_points":proof,
            "return":float(gain[tuple(decisions)]-SIGNAL_COST*sum(chosen))}


def run():
    torch.set_num_threads(1)
    w_signal,w_send,trace=train()
    test=[]
    for public in range(16):
        weights=(7,7,7)
        rows=[inspect(public,weights,c,w_signal,w_send) for c in CAPS]
        bound,fixed,optimal=optimize(public,weights)
        earned=float(np.mean([r["return"] for r in rows]))
        assert earned<=optimal+1e-9 and bound<=optimal+1e-9
        test.append({"public":public,"learned":earned,"no_signal_optimal":bound,
                     "always_announce_optimal_followup":fixed,"signal_optimal":optimal,"worlds":rows})
    summary={k:float(np.mean([r[k] for r in test])) for k in
             ("learned","no_signal_optimal","always_announce_optimal_followup","signal_optimal")}
    return {"seed":SEED,"training_instances":224,"updates":trace,"signal_coefficients":w_signal.tolist(),
            "block_coefficients":w_send.tolist(),"signal_cost":SIGNAL_COST,"message_cost":base.MESSAGE_COST,
            "sudan_source_sha256":sha256(base.CASE.read_bytes()).hexdigest(),"summary":summary,"masks":test}


if __name__=="__main__":
    print(json.dumps(run(),indent=2))
