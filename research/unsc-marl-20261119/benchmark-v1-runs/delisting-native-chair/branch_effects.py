"""Attribute the fixed team's writer gap to individual native receipt sets."""
from collections import defaultdict
from itertools import product
import json

from collect_chair import BASE, HERE, read


def run():
    native = read(HERE/"results.json")
    reference = read(BASE/"results.json")
    case = read(BASE/"case.json")
    slots = (list(case["early"]), list(case["late"]))
    view_to_observation = {"malta":1,"a3plus":2,"switzerland":1}
    mean_mass = defaultdict(float)
    settings = [r for r in reference["native"]["held"] if r["family"]=="2744"]
    assert len(settings)==96
    for row in settings:
        policy = row["native_fit"]
        q0, q1 = row["q_first"], row["q_reply"]
        for view, front, back in product(range(3), range(2), range(2)):
            send = q0*policy["send"][view]
            mass = row["private_prior"][view]*(send if front else 1-send)*(q1 if back else 1-q1)
            early = slots[0][view] if front else None
            observation = view_to_observation[early] if front else 0
            late = slots[1][policy["reply"][observation]] if back else None
            mean_mass[f"{early}/{late}"] += mass/len(settings)
    assert abs(sum(mean_mass.values())-1)<1e-12
    scores=native["scores"]
    table={}
    for key, val in scores.items():
        early,late=key.split("/")
        if early=="None":
            typed=30 if late=="None" else 40
        elif late=="None":
            typed=42
        else:
            typed=reference["records"][key]["audited"]
        table[key]={"mean_receipt_probability":mean_mass[key],"typed":typed,"native":val["released"],
                    "contribution_to_utility_change":mean_mass[key]*(val["released"]-typed)}
    delta=sum(row["contribution_to_utility_change"] for row in table.values())
    expected=native["native_writer"]["released"]["summary"]["native_fit"]-native["typed_reference"]["native_fit"]
    assert abs(delta-expected)<1e-7
    return {"change_in_mean_trained_utility":delta,"receipt_contributions":table}


if __name__=="__main__":
    print(json.dumps(run(),indent=2))
