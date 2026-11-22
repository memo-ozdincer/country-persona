"""Retrain the relay with exact validity confined to the team reward."""
import json
from pathlib import Path
from unittest.mock import patch

import torch

import relay_marl as baseline

ROOT=baseline.HERE/"crossbench"
VENEZUELA=ROOT/"venezuela/case.json"
SPACE=ROOT/"space/case.json"
READINGS=ROOT/"venezuela/evidence/model-receipt/metrics.json"
ORIGINAL=baseline.chair_rows


def raw_signs(task,left,right):
    actions,rows=ORIGINAL(task,left,right)
    # Match the original network topology and initialization. Column 6 no
    # longer tells the chair which particular action is warranted.
    return actions,[(*row[:6],0.,*row[7:]) for row in rows]


def test_families():
    named=baseline.fixtures()
    definitions=json.loads(VENEZUELA.read_text())
    probabilities=json.loads(READINGS.read_text())
    signs=probabilities["conditions"]["pooled"]["signs_before_admission"]
    options=definitions["options"]
    names=tuple(row["id"] for row in options)
    assert all(isinstance(v,bool) for options_by_role in signs.values() for v in options_by_role.values())

    def mask(predicate):
        return sum(1<<i for i,o in enumerate(options) if predicate(o))

    usa=mask(lambda o:signs["us"][o["id"]])
    broad=mask(lambda o:signs["us"][o["id"]] and o["scope"]=="broad")
    russian=tuple(mask(lambda o:signs[card][o["id"]]) for card in ("ru-overlap","ru-impasse"))
    named["venezuela"]=baseline.Task(
        "fictional human-needs recommendation",(*names,"impasse"),(usa,broad),russian,
        (("public by the second cycle","public in the first cycle"),("allows staged public aggregates","confidential throughout")))
    assert [named["venezuela"].valid(a,b) for a,b in named["venezuela"].worlds]==[{1},{7},{7},{7}]

    outer=json.loads(SPACE.read_text())
    names=tuple(o["id"] for o in outer["options"])

    def select(ids):
        return sum(1<<i for i,k in enumerate(names) if k in ids)

    named["outer_space"]=baseline.Task("fictional procedural drafting options",(*names,"impasse"),
        (select("ADF"),select("AD")),(select("BFG"),select("BG")),
        (("study or negotiation with staged scope","study only"),("broad now or staged","broad in first phase")))
    assert [named["outer_space"].valid(a,b) for a,b in named["outer_space"].worlds]==[{5},{7},{7},{7}]
    return named


def judge_weights(archive):
    trained, other=test_families(), {}
    for arm, report in archive["arms"].items():
        actor=baseline.Actor()
        actor.load_state_dict({k:torch.tensor(v) for k,v in report["weights"].items()})
        with torch.no_grad():
            other[arm]={family:{
                control:[baseline.rollout(actor,task,world,channel=control,greedy=True)[0]
                         for world in task.worlds]
                for control in ("peer","mute_far","mute_near","mute_both")}
                for family,task in trained.items() if family not in ("mali","myanmar")}
    return other


def run(original_results):
    original_results = json.loads(Path(original_results).read_text())
    exact_external = judge_weights(original_results)
    with patch.object(baseline,"chair_rows",new=raw_signs):
        training = baseline.cross_validate()
        raw_external = judge_weights(training)
    return {"scope":"Same seed, examples and model architecture. Only the precomputed per-action warrant input is ablated. Warrant remains an environment-side evaluation and reward. The larger linked tasks are fictional controlled variants.",
            "same_fixture_holdout":training,"larger_linked_families":{"with_warrant_observation":exact_external,"raw_signs":raw_external}}


if __name__=="__main__":
    import sys

    print(json.dumps(run(sys.argv[1]),indent=2))
