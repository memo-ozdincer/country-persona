"""Remove sampling variance from both policy gradients as a diagnostic."""
from itertools import product
import json

import numpy as np

from experiment import CHECKPOINTS, HERE, PREVIOUS, fit, send_audit, team


def train(table):
    public, first, last, both, observed = table
    grid = np.array(list(product(range(2), range(3), team.TRAIN_DELIVERY,
                                 team.TRAIN_DELIVERY, team.TRAIN_PRICES)))
    docket, view = grid[:, :2].astype(int).T
    q0, q1, price = grid[:, 2:].T
    obs = observed[docket, view]
    x = team.features(q0, q1, price)
    sender = np.zeros((2, 3, 5))
    reply = np.zeros((2, 3))
    s1, s2 = np.zeros_like(sender), np.zeros_like(sender)
    r1, r2 = np.zeros_like(reply), np.zeros_like(reply)
    history = []
    size = len(grid)
    for step in range(1, team.UPDATES+1):
        p_send = team.sigmoid(np.sum(sender[docket, view] * x, axis=1))
        p_silent = team.sigmoid(reply[docket, 0])
        p_arrived = team.sigmoid(reply[docket, obs])
        absent_gain = q1*(last[docket, 1]-last[docket, 0])
        present_gain = q1*(both[docket, view, 1]-both[docket, view, 0])
        absent = (1-q1)*public[docket]+q1*last[docket, 0]+p_silent*absent_gain
        present = (1-q1)*first[docket, view]+q1*both[docket, view, 0]+p_arrived*present_gain
        send_gain = q0*(present-absent)-price
        arrived = p_send*q0
        grad_s, grad_r = np.zeros_like(sender), np.zeros_like(reply)
        np.add.at(grad_s, (docket, view),
                  x*(p_send*(1-p_send)*send_gain)[:, None]/(10*size))
        np.add.at(grad_r, (docket, np.zeros_like(docket)),
                  (1-arrived)*p_silent*(1-p_silent)*absent_gain/(10*size))
        np.add.at(grad_r, (docket, obs),
                  arrived*p_arrived*(1-p_arrived)*present_gain/(10*size))
        sender, s1, s2 = team.adam(sender, grad_s, s1, s2, step)
        reply, r1, r2 = team.adam(reply, grad_r, r1, r2, step)
        if step in CHECKPOINTS:
            history.append({"update": step, "expected_training_utility": float(np.mean(absent+p_send*send_gain)),
                            "sender": sender.round(10).tolist(), "receiver": reply.round(10).tolist()})
    return sender, reply, history


def run():
    old = fit.read(PREVIOUS / "results.json")
    banks, _ = fit.tables(old["grades"])
    weights = tuple(np.array(old["history"][-1][key]) for key in ("sender", "receiver"))
    sender, reply, history = train(banks["trusted_native"])
    report = fit.compare(banks["audited_native"], (sender, reply), weights)
    return {"history": history, "evaluation": report,
            "sender_mismatches": send_audit(banks["audited_native"], report["held"])}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
