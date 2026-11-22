"""Apply a frozen routing policy to all offered openings in one UNBench workshop."""
from collections import Counter
from hashlib import sha256
from itertools import product
from pathlib import Path
import argparse
import json
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2]))
from decision_ledger import readout

from environment import simulate
from guard import guarded
from joint import restore, roll


def project(options, card):
    return sum(1 << i for i, o in enumerate(options) if all(o[key] == value for key, value in card.items()))


def evaluate(path, scenario_path=HERE / "sanctions.json"):
    scenario = json.loads(scenario_path.read_text())
    options = scenario["options"]
    labels = [o["id"] for o in options]
    n = len(options)
    roles = scenario["roles"]
    chooser = guarded(restore(json.loads(path.read_text())))
    outcomes = []
    counts = Counter()
    for name, cards in scenario["variants"].items():
        local_menus = tuple(project(options, card) for card in cards)
        assert bool(local_menus[0] & local_menus[1]) == (name == "overlap")
        positives = [[1 << i for i in range(n) if menu & (1 << i)] for menu in local_menus]
        for a, b in product(*positives):
            opening = (a,0,b,0)
            for arm in ("script","guarded"):
                result, moves = (simulate(n,local_menus,opening,"flexible") if arm == "script"
                                 else roll(n,local_menus,opening,chooser))
                trace = [(0,a,True,1), (1,b,True,1), *moves]
                claims = []
                for i, (role, bit, sign, _) in enumerate(trace):
                    assert sign == bool(local_menus[role] & bit)
                    if bit:
                        letter = labels[bit.bit_length()-1]
                        claims.append({"id":f"claim-{i+1}", "role":roles[role],
                                       "accepts":[letter] if sign else [], "excludes":[] if sign else [letter]})
                public = readout(labels,roles,claims)
                assert result == (public["state"] == ("AGREEMENT_POSSIBLE" if name == "overlap" else "IMPASSE"))
                counts[(name,arm,"certified")] += result
                counts[(name,arm,"total")] += 1
                counts[(name,arm,"continuation_slots")] += len(moves)
                outcomes.append({"variant":name, "opening":[labels[x.bit_length()-1] for x in (a,b)],"arm":arm,
                                 "public_claims":claims,"readout":public,"continuation_slots":len(moves)})
    return {"scope":scenario["status"],"scenario_sha256":sha256(scenario_path.read_bytes()).hexdigest(),
            "policy_sha256":sha256(path.read_bytes()).hexdigest(),
            "metrics":{"/".join(k):v for k,v in counts.items()},"replays":outcomes}


if __name__ == "__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("policy",type=Path)
    print(json.dumps(evaluate(p.parse_args().policy),indent=2))
