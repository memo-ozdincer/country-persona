"""Replay a fixed half-forced query mixture and audit decisions by branch."""
from collections import Counter
from pathlib import Path
from unittest.mock import patch

import torch

import study

HERE = study.HERE
ORIGINAL = study.weighted_team


def mixed(p, s, sign, delta, base):
    forced = torch.zeros_like(p)
    forced[:, 1:] = .25
    return ORIGINAL(.5*p + forced, s, sign, delta, base)


def response_error(rows, weights):
    x, y, sign, delta, _ = study.tensors(rows)
    chief, emitter = study.policies(x, y, *weights)
    result = Counter()
    for i, r in enumerate(rows):
        target = int(chief[i].argmax()) - 1
        if target == -1:
            continue
        for answer in (0, 1):
            if not sign[i, target, answer]:
                continue
            actual = bool(emitter[i, target, answer] > .5)
            preferred = bool(delta[i, target, answer] > 0.)
            if actual != preferred:
                result[f"{r['mode']}/{'avoidable_send' if actual else 'missed_send'}"] += 1
    return dict(result)


def reversal(rows):
    by_context = {(r["family"], r["mode"], r["order"], tuple(r["prior"]), tuple(r["delivery"])): r for r in rows}
    keys = list(by_context)
    output = Counter()
    for key in keys:
        reverse = (*key[:-1], key[-1][::-1])
        if key[-2] > key[-2][::-1] or key[-1] >= reverse[-1] or key[1] != "two_openings":
            continue
        a, b = by_context[key], by_context[reverse]
        exact = [x["arms"]["exact_public_oracle"]["question"] for x in (a, b)]
        if "quiet" in exact or exact[0] == exact[1]:
            continue
        output["pairs"] += 1
        for name in a["arms"]:
            choices = [x["arms"][name]["question"] for x in (a, b)]
            if choices == exact:
                output[name] += 1
    return dict(output)


def run():
    torch.set_num_threads(1)
    baseline_path = HERE / "results.json"
    old = study.benchmark.read(baseline_path)
    dev, test = study.roster()
    with patch.object(study, "weighted_team", mixed):
        cw, rw, trace = study.fit(dev)
    old_weights = tuple(torch.tensor(w, dtype=study.DTYPE) for w in old["weights"])
    after = study.evaluate(test, (cw, rw))
    assert len(old["test_states"]) == len(after)
    for before, new in zip(old["test_states"], after, strict=True):
        for mode in ("exact_public_oracle", "proof_first", "probability_product"):
            assert before["arms"][mode] == new["arms"][mode]
    return {"training_trace": trace, "learned_weights": [cw.tolist(), rw.tolist()],
            "before": {"aggregate": old["test"], "response_errors": response_error(test, old_weights),
                       "reversal": reversal(old["test_states"])},
            "after": {"aggregate": study.aggregate(after), "response_errors": response_error(test, (cw, rw)),
                      "reversal": reversal(after)},
            "inputs_sha256": {p.name: study.sha256(p.read_bytes()).hexdigest() for p in (
                baseline_path, Path(__file__), HERE / "reply-coverage-protocol.md")}}


if __name__ == "__main__":
    study.benchmark.emit(run())
