"""Swap trained teammates under the same relay and private-card contracts."""
from itertools import product
import json
from pathlib import Path
import sys
from unittest.mock import patch

import torch

import relay_marl as core
import relay_raw_signs as observed

MODES=("outcome","warranted")


class Mixed:
    def __init__(self, actors, composition):
        self.actors=actors
        self.composition=composition

    def distribution(self,kind,rows):
        # The shared communication model receives a one-hot round marker.
        # It selects a named seat here without inspecting the private cards.
        slot=2 if kind=="chair" else 0 if rows[0][1] else 1
        return self.actors[self.composition[slot]].distribution(kind,rows)


def evaluate(source):
    torch.set_num_threads(1)
    fitted=json.loads(source.read_text())
    policies={}
    for kind,data in fitted["results"]["arms"].items():
        actor=core.Actor()
        actor.load_state_dict({k:torch.tensor(v) for k,v in data["weights"].items()})
        policies[kind]=actor
    tables={}
    with patch.object(core,"chair_rows",new=observed.raw_signs),torch.no_grad():
        for family,task in observed.test_families().items():
            tables[family]={}
            for assignment in product(MODES,repeat=3):
                results=[core.rollout(Mixed(policies,assignment),task,world,greedy=True)[0]
                         for world in task.worlds]
                measures={k:sum(int(r[k]) for r in results)
                          for k in ("valid","warranted","both_sources","messages")}
                tables[family]["/".join(assignment)]={"metrics":measures,"episodes":results}
    return {"scope":"Frozen cross-play of two trained actors. Same synthetic training seed and different reward objectives; the held-out role assignments are never used for fitting.",
            "assignment_order":["far delegate","relay","chair"],"families":tables}


if __name__=="__main__":
    print(json.dumps(evaluate(Path(sys.argv[1])),indent=2))
