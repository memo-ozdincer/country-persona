"""Render role-scoped, source-linked records from actual admitted disclosures."""
import argparse
import json
from pathlib import Path

from episode import readout, source_paths

CONVENERS = {"monitoring-team":"Monitoring Team","erc":"ERC","committee":"committee"}
TRACKS = {"renewed-review":"keep renewed membership review on the agenda",
          "briefings-only":"limit the agenda to briefings","hold-agenda":"hold the membership agenda"}
SEQUENCES = {"parallel":"in parallel with work on a humanitarian pause",
             "pause-first":"after first addressing a humanitarian pause"}


def render(case, claims, proof):
    roles = case["roles"]
    names = [r.removesuffix(" workshop delegate") for r in roles]
    options = {o["id"]:o for o in case["options"]}
    assert readout(options,roles,claims)==proof
    state = proof["state"]
    by_id = {c["id"]:c for c in claims}
    refs = {}
    if state=="AGREEMENT_POSSIBLE":
        option, assigned = next(iter(proof["verified_options"].items()))
        package = options[option]
        if "convener" in package:
            interval = "annually" if package["interval"]=="annual" else f"every {package['interval']}"
            evidence = (f"Package {option} proposes that the {CONVENERS[package['convener']]} convene, "
                        f"with {package['public_report']} public reporting {interval}.")
        else:
            evidence = (f"Package {option} would {TRACKS[package['track']]} {SEQUENCES[package['sequence']]}. "
                        f"The proposed product is {package['product']}.")
        state = f"{state} {option}"
        refs = {role:ids[0] for role,ids in assigned.items()}
    elif state=="IMPASSE":
        blocked = proof["blocked_options"]
        evidence = f"Every one of the {len(blocked)} offered packages was excluded by at least one delegate."
        for role in roles:
            candidates = [i for signs in blocked.values() for i in signs.get(role,[])]
            if candidates:
                refs[role] = candidates[-1]
    else:
        assert state=="UNRESOLVED"
        missing = []
        for option in proof["unresolved_options"]:
            absent = [name for role,name in zip(roles,names,strict=True) if not any(
                c["role"]==role and option in c["accepts"]+c["excludes"] for c in claims)]
            if absent:
                missing.append(f"Package {option} lacks a disclosure from {' and '.join(absent)}.")
        evidence = " ".join(missing)
        for role in roles:
            outstanding = [c["id"] for c in claims if c["role"]==role and
                           any(o in proof["unresolved_options"] for o in c["accepts"])]
            if outstanding:
                refs[role] = outstanding[-1]

    support = []
    for role,name in zip(roles,names,strict=True):
        ref = refs.get(role) or next((c["id"] for c in claims if c["role"]==role),None)
        if not ref:
            support.append(f"No signed workshop claim from {name} entered the ledger.")
            continue
        row = by_id[ref]
        assert row["role"]==role
        sign, letter = next((f,v[0]) for f,v in (("accepts",row["accepts"]),("excludes",row["excludes"])) if v)
        support.append(f"{name} {sign} {letter} in the workshop ({ref}).")

    historic = {item["id"]:item["fact"] for item in case["historical"]}
    if "india" in historic:
        roll = historic["roll"].replace("the draft",f"draft {case['draft']}",1)
        history = f"{roll} {historic['india']}"
        authority = "Workshop proposals are fictional. They neither amend the resolution nor record an official decision."
    else:
        history = " ".join(historic[k] for k in ("roll","france","uk"))
        authority = ("The draft would recommend admission. A Council recommendation precedes the General Assembly’s "
                     "decision under Article 4. Workshop notes confer neither membership nor bilateral recognition.")
    return "\n".join((f"History: {history}",f"Workshop: {state}",f"Evidence: {evidence}",
                      "Positions: "+" ".join(support),f"Authority: {authority}"))


def compose(result):
    paths = source_paths()
    cases = {k:json.loads(paths[k].read_text()) for k in ("sanctions","membership")}
    records = {}
    for name, row in result["episodes"].items():
        case = cases[name.split("/")[0]]
        memo = render(case,row["claims"],row["readout"])
        records[name] = {"record":memo,"words":len(memo.split()),"state":row["readout"]["state"]}
    return records


if __name__=="__main__":
    arg = argparse.ArgumentParser(description=__doc__)
    arg.add_argument("metrics",type=Path)
    args=arg.parse_args()
    print(json.dumps(compose(json.loads(args.metrics.read_text())),indent=2,ensure_ascii=False))
