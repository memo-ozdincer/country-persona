"""Verify signed compatibility locally before admitting it to the public ledger."""
import json

import fit
import cases

HERE, E = cases.HERE, cases.E


def verified_sign(public_options, own_requirement, candidate):
    """Read only the replying role's card and the published package properties."""
    package, = [row for row in public_options if row["id"] == candidate]
    if not own_requirement or not set(own_requirement) <= package.keys():
        raise ValueError("Unrecognized private requirement field")
    return "Y" if all(package[field] == value for field, value in own_requirement.items()) else "N"


def signature(row):
    case_id, *_ = row["id"].split("/")
    menu = E.cases()[case_id]["options"]
    user = json.loads(row["messages"][1]["content"])
    local = dict(t.split(" must be ", 1) for t in user["my_full_fictional_requirement"].split(", "))
    assert user["query_package"] == row["target"]
    assert user["possible_packages"] == [{"package": p["id"], "proposal": p["text"]} for p in menu]
    return verified_sign(menu, local, user["query_package"])


def run():
    fits, factors = [E.read(HERE / name) for name in ("results.json", "factor.json")]
    held = cases.roster()["held"]
    prior = {r["id"]: r for r in held}
    records = {}
    for name, row in fits["evaluation"]["held"]["rows"].items():
        observation = prior[name]
        sign = signature(observation)
        assert (sign == "Y") == observation["truth"]
        verdict = {}
        estimates = {k: row["arms"][k]["selected"] for k in ("frozen", "residual")}
        estimates["trained_sign"] = factors["rows"][name]["arms"]["trained_sign"]["selected"]
        estimates["exact"] = row["arms"]["exact"]["selected"]
        for arm, raw in estimates.items():
            outputs = {"reject": "P" if raw not in {"P", sign} else raw,
                       "complete_sign": sign if raw != "P" else raw}
            exact = estimates["exact"]
            for condition, action in outputs.items():
                audit = observation["audit"][action]
                assert audit["truthful"] and not audit["wrong_commit"]
                verdict[f"{arm}/{condition}"] = {"selected": action, **audit,
                    "best_response": action == exact, "missed_proof": action == "P" and exact != "P",
                    "avoidable_send": action != "P" and exact == "P",
                    "net": observation["utility"][cases.DEC.index(action)],
                    "changed": action != raw}
        records[name] = {"family": observation["family"], "mode": observation["mode"], "arms": verdict}
    changed = {arm: sum(r["arms"][arm]["changed"] for r in records.values())
               for arm in next(iter(records.values()))["arms"]}
    return {"summary": fit.aggregate(records), "changed": changed, "episodes": records,
            "sha256": {key: fit.digest(HERE / key) for key in ("results.json", "factor.json", "local-guard-protocol.md",
                                                             "local_guard.py")}}


if __name__ == "__main__":
    E.emit(run())
