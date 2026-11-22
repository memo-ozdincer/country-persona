"""Check the positivity-handoff rule on the established complete-menu grid."""
from collections import Counter
import json

from partial_dispatch import simulate, source_paths, restore, guarded
from environment import presentations


def check(n=6):
    options = "ABCDEFG"[:n]
    full = (1 << n)-1
    generic = {"options":[{"id":c} for c in options], "roles":["A","B"]}
    choose = guarded(restore(json.loads(source_paths()["policy"].read_text())))
    counts = Counter()
    for world, state in presentations(n):
        opening = tuple(options[state[i].bit_length()-1] for i in (0,2))
        signed = tuple((menu,full & ~menu) for menu in world)
        label = "agreement" if world[0]&world[1] else "impasse"
        for arm in ("script","learned"):
            before,after=(simulate(generic,opening,signed,world,arm,choose,v) for v in (False,True))
            a,b = (row["readout"]["state"]!="UNRESOLVED" for row in (before,after))
            counts[(arm,label,"cases")] += 1
            counts[(arm,label,"original_certified")] += a
            counts[(arm,label,"modified_certified")] += b
            counts[(arm,label,"lost")] += a and not b
            counts[(arm,label,"gained")] += b and not a
            counts[(arm,label,"original_slots")] += len(before["events"])-2
            counts[(arm,label,"modified_slots")] += len(after["events"])-2
    return {"options":n,"counts":{"/".join(k):v for k,v in counts.items()}}


if __name__=="__main__":
    print(json.dumps(check(),indent=2))
