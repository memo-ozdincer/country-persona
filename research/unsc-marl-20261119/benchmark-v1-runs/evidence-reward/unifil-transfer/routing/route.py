"""Choose a role and package from the public proof state, then replay the reply."""
from collections import Counter
from hashlib import sha256
from itertools import product
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
BENCH = HERE.parent
sys.path.insert(0, str(BENCH))
import audit as a
import transfer_fit as fitted

E, ROLES, OPTIONS = a.E, a.ROLES, a.OPTIONS
RATES = (.08, .8)
ASK, SEND = .04, a.SEND
TOLERANCE = 1e-10
ARMS = {
    "decision_rule": ("decision", "decision"),
    "exact_record": ("record", "record"),
    "learned_chair": ("learned", "record"),
    "learned_team": ("learned", "learned"),
}


def context(menu, log, tree):
    seen, points, candidates = a.state(menu, log)
    values = {}
    for role, option in product(ROLES, OPTIONS):
        compatible = [option in a.accepted(menu, req) for req in candidates[role]]
        other = ROLES[1-ROLES.index(role)]
        if_true = {}
        for sign in sorted(set(compatible)):
            next_log = log + [a.public.signed.claim("reply", role, sign, option)]
            decision, new_points, posterior = a.state(menu, next_log)
            features = (*a.public.features(log, role, option, 1., sign),
                        float(len(candidates[role]) == 1), float(len(candidates[other]) == 1),
                        float(len(posterior[role]) == 1))
            proof = decision != "UNRESOLVED"
            if_true[sign] = {
                "probability": compatible.count(sign)/len(compatible),
                "decision": float(proof and seen == "UNRESOLVED"),
                "record": new_points-points,
                "learned": fitted.predict(tree, features),
                "status": decision,
            }
        values[role, option] = if_true
    return seen, values


def choice(values, rate, objective, recipient_policy=None):
    best, forecast = None, 0.
    for query, branches in values.items():
        total = 0.
        for sign, branch in branches.items():
            del sign
            gate = recipient_policy or objective
            send = rate*branch[gate] - SEND > TOLERANCE
            total += branch["probability"] * (rate*branch[objective] - SEND if send else 0.)
        net = total-ASK
        if net > forecast + TOLERANCE:
            best, forecast = query, net
    return best, forecast


def outcome(query, predicted, values, rate, local, receiver):
    if query is None:
        return {"question": None, "sent":False, "score_gain":0., "proof_gain":0., "cost":0., "net":0., "projected":0.}
    role, option = query
    sign = option in local[ROLES.index(role)]
    branch = values[query][sign]
    sent = rate*branch[receiver] - SEND > TOLERANCE
    charge = ASK + SEND*sent
    gained = rate*branch["record"]*sent
    return {"question": list(query), "sent": sent, "score_gain": gained, "proof_gain": rate*branch["decision"]*sent,
            "cost": charge, "net": gained-charge, "projected": predicted,
            "truthful_reply": sign, "after_if_delivered": branch["status"]}


def run():
    config = E.read(BENCH/"case.json")
    tree = E.read(BENCH/"transfer-fit.json")["tree"]
    menu = config["menu"]
    stages = {}
    context_receipts = {}
    repeated = 0
    for rate in RATES:
        totals = {arm: Counter() for arm in ARMS}
        worlds = {}
        differing = []
        for world in config["worlds"]:
            local = [a.accepted(menu, req) for req in world["requirements"]]
            claims = [a.public.signed.claim(f"{i}/{opt}", role, opt in local[i], opt)
                      for i, role in enumerate(ROLES) for opt in OPTIONS]
            public_count = Counter()
            for subset in a.subsets(claims):
                log = list(subset)
                prior, values = context(menu, log, tree)
                choices = {}
                for arm, (chair, responder) in ARMS.items():
                    # The learned chair with exact recipient is a swap.
                    # Give it the same predicted recipient during planning
                    # as the complete learned policy, without oracle hints.
                    best, expected = choice(values, rate, chair)
                    choices[arm] = outcome(best, expected, values, rate, local, responder)
                    row = choices[arm]
                    totals[arm]["questions"] += row["question"] is not None
                    totals[arm]["sent"] += row["sent"]
                    for key in ("proof_gain","score_gain","cost","net","projected"):
                        totals[arm][key] += row[key]
                signature = E.checksum([rate, log])
                selections = {arm: row["question"] for arm,row in choices.items()}
                if signature in context_receipts:
                    assert context_receipts[signature] == selections
                    repeated += 1
                context_receipts[signature] = selections
                public_count["openings"] += 1
                public_count["decision_unresolved"] += prior == "UNRESOLVED"
                same = choices["learned_team"]["question"] == choices["exact_record"]["question"]
                public_count["learned_query_disagrees_with_exact"] += not same
                if not same:
                    differing.append({"world": world["id"], "signs": log, "prior":prior, "arms":choices})
            worlds[world["id"]] = public_count
        assert sum(row["openings"] for row in worlds.values()) == 768
        stages[str(rate)] = {"totals": totals, "worlds": worlds, "query_differences": differing}
    files = (Path(__file__), HERE/"protocol.md", BENCH/"case.json", BENCH/"transfer-fit.json",
             BENCH/"transfer_fit.py", BENCH/"audit.py")
    return {"opening_world_presentations_per_rate":768, "repeated_public_state_checks": repeated,
            "results": stages, "sha256": {p.name: sha256(p.read_bytes()).hexdigest() for p in files}}


if __name__ == "__main__":
    E.emit(run())
