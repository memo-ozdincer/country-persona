"""Replay the scope-policy fit and compare alternative fixed check schedules."""
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import random

import scope_policy as routing

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "evidence/scope-policy"


class Rule:
    def __init__(self, choose):
        self.choose = choose

    def get(self, observation, _):
        return self.choose(observation)


def compare(heldout, trained):
    alternatives = {
        "check_when_legal": Rule(lambda _: True),
        "check_unless_matching_peer_offer": Rule(lambda obs: obs[6] != 0),
        "check_unless_matching_peer_offer_or_one_unknown": Rule(lambda obs: obs[6] != 0 and obs[2] >= 2),
    }
    learned, _ = routing.stats(heldout, trained)
    output = {}
    for name, rule in alternatives.items():
        baseline, scores = routing.stats(heldout, rule)
        paired = Counter()
        for row, a, b in zip(heldout, baseline, learned, strict=True):
            category = "agreement" if row[1][0] & row[1][1] else "impasse"
            paired[category, str(a), str(b)] += 1
        output[name] = {"scores": routing.flatten(scores), "learned_pairs": routing.flatten(paired)}
    return output


def main():
    launch = json.loads((SOURCE / "launch.json").read_text())
    for name, expected in launch["sha256"].items():
        assert sha256((HERE.parents[1] / name).read_bytes()).hexdigest() == expected
    archive = json.loads((SOURCE / "results.json").read_text())
    assert json.loads(json.dumps(routing.study())) == archive
    policy = {tuple(key): val for key, val in archive["policy"]}
    heldout = routing.panels((6, 7), routing.TEST_SEED, 1200, 3)
    rnd = random.Random(routing.TEST_SEED + 1)
    lost = [(*row[:-1], tuple(mask if rnd.random() >= .25 else 0 for mask in row[-1])) for row in heldout]
    print(json.dumps({"launch_hashes": len(launch["sha256"]), "exact_fit_and_heldout_replay": True,
                      "reliable": compare(heldout, policy), "missing_returns": compare(lost, policy)}, indent=2))


if __name__ == "__main__":
    main()
