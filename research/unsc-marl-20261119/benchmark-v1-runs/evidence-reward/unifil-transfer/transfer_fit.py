"""Fit a small counterfactual value tree without fitting on the UNIFIL family."""
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path

import audit as a

HERE = Path(__file__).resolve().parent
DEPTH = 6


def typed_worlds():
    source = a.E.read(a.public.signed.SIGNED/"roster.json")["train"]
    groups = {}
    for row in source:
        name = row["id"].split("/")[0]
        payload = json.loads(row["messages"][1]["content"])
        assert name.startswith("synthetic-")
        menu = [{"id": p["package"], **dict(t.split(" is ", 1) for t in p["proposal"].split("; "))}
                for p in payload["possible_packages"]]
        item = groups.setdefault(name, (menu, {}))
        left, right = payload["my_full_fictional_requirement"].split(" must be ", 1)
        assert item[0] == menu
        assert item[1].setdefault(payload["you"], {left: right}) == {left: right}
    assert len(groups) == 16 and all(set(row[1]) == set(a.ROLES) for row in groups.values())
    return [{"id": key, "menu": menu, "requirements": [req[r] for r in a.ROLES]}
            for key, (menu, req) in groups.items()]


def candidates(menu, log):
    field_names = [key for key in menu[0] if key != "id"]
    possible = [(req, a.accepted(menu, req)) for req in (
        {field: value} for field in field_names for value in sorted({p[field] for p in menu})
    )]
    return {role: [req for req, match in possible if all(
        set(r.get("accepts", ())) <= match and not set(r.get("excludes", ())) & match
        for r in log if r["role"] == role)] for role in a.ROLES}


def score_before(proof, known):
    return 0. if proof["state"] == "UNRESOLVED" else 1. if known else 1-a.BONUS


def world_rows(world):
    menu = world["menu"]
    cards = world["requirements"]
    sets = [a.accepted(menu, req) for req in cards]
    triples = [(role, opt, a.public.signed.claim(f"{i}/{opt}", role, opt in sets[i], opt))
               for i, role in enumerate(a.ROLES) for opt in a.OPTIONS]
    for log in a.subsets([claim for _,_,claim in triples]):
        options = candidates(menu, log)
        display = a.public.signed.chair.readout(a.OPTIONS, a.ROLES, log)
        assert all(card in options[role] for role, card in zip(a.ROLES, cards, strict=True))
        before = score_before(display, all(len(c) == 1 for c in options.values()))
        for role, opt, claim in triples:
            sign = bool(claim.get("accepts"))
            other = a.ROLES[1-a.ROLES.index(role)]
            after_role = [req for req in options[role] if (opt in a.accepted(menu, req)) == sign]
            projected = (*a.public.features(log, role, opt, 1., sign),
                         float(len(options[role]) == 1), float(len(options[other]) == 1),
                         float(len(after_role) == 1))
            after_log = [*log, {**claim, "id": "reply"}]
            proof = a.public.signed.chair.readout(a.OPTIONS, a.ROLES, after_log)
            after = score_before(proof, len(after_role) == len(options[other]) == 1)
            assert after >= before
            yield projected, round(after-before, 10)


def branch_error(rows):
    n = sum(w for _,_,w in rows)
    if not n:
        return 0., 0.
    mean = sum(y*w for _,y,w in rows)/n
    return sum((y-mean)**2*w for _,y,w in rows), mean


def fit(rows, depth):
    initial_error, mean = branch_error(rows)
    if depth == 0 or initial_error < 1e-12:
        return {"prediction": mean, "weighted_rows": sum(w for _,_,w in rows)}
    best = None
    for index in range(len(rows[0][0])):
        grid = sorted({x[index] for x,_,_ in rows})
        for low, high in zip(grid, grid[1:]):
            threshold = (low+high)/2
            left = [r for r in rows if r[0][index] <= threshold]
            right = [r for r in rows if r[0][index] > threshold]
            error = branch_error(left)[0] + branch_error(right)[0]
            if best is None or (error, index, threshold) < best[:3]:
                best = (error,index,threshold,left,right)
    if best is None or best[0] >= initial_error - 1e-12:
        return {"prediction": mean, "weighted_rows": sum(w for _,_,w in rows)}
    _, index, threshold, left, right = best
    return {"feature": index, "threshold": threshold, "left": fit(left, depth-1),
            "right": fit(right, depth-1)}


def predict(tree, row):
    if "prediction" in tree:
        return tree["prediction"]
    side = "left" if row[tree["feature"]] <= tree["threshold"] else "right"
    return predict(tree[side], row)


def run():
    train = typed_worlds()
    observations = Counter(item for world in train for item in world_rows(world))
    tree = fit([(x,y,w) for (x,y),w in sorted(observations.items())], DEPTH)
    events = a.E.read(HERE/"case.json")
    held = [item for world in events["worlds"] for item in world_rows({**world, "menu": events["menu"]})]
    reports = {}
    supported = {x for x,_ in observations}
    for rate in a.RATES:
        errors = frequencies = unrepresented = 0
        fitted = best = 0.
        for x, true in held:
            oracle = rate*true-a.SEND
            margin = rate*predict(tree,x)-a.SEND
            sends = margin > 1e-10
            errors += sends != (oracle > 1e-10)
            frequencies += sends
            unrepresented += x not in supported
            fitted += sends*oracle
            best += max(0.,oracle)
        reports[str(rate)] = {"sends": frequencies, "action_errors": errors, "net": fitted,
                              "oracle_net": best, "regret": best-fitted, "unseen_input_combinations": unrepresented}
    paths = (Path(__file__), HERE/"audit.py", HERE/"case.json", HERE/"transfer-fit-protocol.md",
             a.public.signed.SIGNED/"roster.json")
    return {"tree": tree, "synthetic_worlds": len(train), "synthetic_rows": sum(observations.values()),
            "held_presentations": len(held), "rates": reports,
            "sha256": {p.name: sha256(p.read_bytes()).hexdigest() for p in paths}}


if __name__ == "__main__":
    a.E.emit(run())
