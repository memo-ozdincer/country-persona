"""Compare fixed policies with a shared prior and audit the value of learned hints."""
from itertools import product
from pathlib import Path
from statistics import mean

import torch

import retry as r

HERE = r.HERE
SELECTABLE = tuple(a for a in r.ARMS if not a.startswith("full_bank"))


def preview_mix(scene):
    bank = scene["bank"]
    mass = sum(r.make(bank, law, .85)["mass"] for law in r.FAMILIES)/2
    return scene | {"mass":mass}


def outcomes(rows, weights, accuracy):
    results = []
    for family,name,law,scene in r.corpus(rows,accuracy):
        model = preview_mix(scene)
        selected = {f"shared_prior/{arm}":r.policy_fixed(model,arm) for arm in SELECTABLE}
        p,q = r.strategy(scene,weights,True)
        selected["learned_without_hints"] = (torch.zeros_like(p),q)
        selected["learned"] = (p,q)
        policies = {}
        for tag,(p,q) in selected.items():
            net,score,tries,hints = [float(x) for x in r.expected(scene,p,q)]
            if tag in ("learned","learned_without_hints"):
                replay = r.independent_check(scene,p,q)
                assert max(abs(a-b) for a,b in zip((net,score,tries,hints),replay,strict=True))<1e-8
            policies[tag] = {"net":net,"release":score,"retries":tries,"hints":hints}
        results.append({"family":family,"bank":name,"law":law,"outcomes":policies,
                        "free_signal_full_bank_ceiling":r.semantic_oracle(scene)})
    return results


def check(fitting, testing, baseline):
    weights = [torch.tensor(w,dtype=r.D) for w in baseline["weights"]]
    trained = r.summarize(outcomes(fitting,weights,.85))
    selected = max((name for name in trained if name.startswith("shared_prior/")),
                   key=lambda arm:trained[arm]["net"])
    tests = {}
    for scenario, p in (("matched",.85),("stressed",.65)):
        rows = outcomes(testing,weights,p)
        archived = baseline["test"][scenario]["rows"]
        for actual, prior in zip(rows,archived,strict=True):
            assert actual["outcomes"]["learned"] == prior["outcomes"]["learned_greedy"]
        summary = r.summarize(rows)
        ceiling = mean(mean(x["free_signal_full_bank_ceiling"] for x in rows if x["family"]==family)
                       for family in sorted({r0["family"] for r0 in rows}))
        envelope = max((arm for arm in summary if arm.startswith("shared_prior/")),
                       key=lambda arm:summary[arm]["net"])
        tests[scenario] = {"rows":rows,"summary":summary,"selected":selected,"envelope":envelope,
                           "free_signal_full_bank_ceiling":ceiling,
                           "net_over_training_selected":summary["learned"]["net"]-summary[selected]["net"],
                           "net_over_shared_envelope":summary["learned"]["net"]-summary[envelope]["net"],
                           "net_from_hints":summary["learned"]["net"]-summary["learned_without_hints"]["net"]}
    return tests


def run():
    torch.set_num_threads(1)
    baseline = r.read(HERE/"results.json")
    train,test = r.point_banks()
    groups = {}
    for name, frozen in baseline["groups"].items():
        if name=="transfer":
            groups[name] = check(train,test,frozen)
        else:
            groups[name] = check([x for x in train if x[0]!=name],[x for x in train if x[0]==name],frozen)
    summary = {}
    for mode in ("matched","stressed"):
        matches = [v[mode] for key,v in groups.items() if key!="transfer"]
        corresponding = [v["test"][mode] for key,v in baseline["groups"].items() if key!="transfer"]
        summary[mode] = {"archive": {
            "mean_net":mean(x["summary"]["learned"]["net"] for x in matches),
            "silent_net":mean(x["summary"]["silent"]["net"] for x in corresponding),
            "known_law_fixed_net":mean(x["fixed_net"] for x in corresponding),
            "shared_prior_fixed_net":mean(x["summary"][x["selected"]]["net"] for x in matches),
            "gain_from_hints":mean(x["net_from_hints"] for x in matches),
            "known_law_fixed_envelope":max(mean(x["summary"][arm]["net"] for x in corresponding) for arm in SELECTABLE),
        },"transfer":{k:v for k,v in groups["transfer"][mode].items() if k!="rows"}}
    pins = (Path(__file__),HERE/"results.json",HERE/"plan.json")
    return {"groups":groups,"summary":summary,"hashes":{p.name:r.digest(p) for p in pins}}


if __name__ == "__main__":
    print(r.json.dumps(run(),indent=2))
