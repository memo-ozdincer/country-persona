"""Plan and audit two contingent queries from UNIFIL public signs."""
from collections import Counter
from functools import lru_cache
from hashlib import sha256
from itertools import product
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import route as r

E, ROLES, OPT = r.E, r.ROLES, r.OPTIONS
ASK, SEND, TOL = r.ASK, r.SEND, r.TOLERANCE
QUERIES = tuple(product(ROLES, OPT))
ARMS = {
    "one_exact": (1, 1, "record", "mandatory"),
    "greedy_two": (2, 1, "record", "mandatory"),
    "two_exact": (2, 2, "record", "mandatory"),
    "two_learned": (2, 2, "learned", "mandatory"),
    "two_exact_myopic_partner": (2, 2, "record", "myopic"),
}


def get_log(state):
    return [r.a.public.signed.claim(str(i), role, token==1, q)
            for i, ((role,q),token) in enumerate(zip(QUERIES,state,strict=True)) if token]


def advance(state, idx, sign):
    token = 1 if sign else -1
    assert state[idx] in (0, token)
    return state[:idx] + (token,) + state[idx+1:]


def fixture(menu, tree, rate):
    @lru_cache(maxsize=None)
    def context(state):
        log = get_log(state)
        decision, outcomes = r.context(menu, log, tree)
        _, terminal, _ = r.a.state(menu, log)
        return decision, terminal, tuple(outcomes[q] for q in QUERIES)

    @lru_cache(maxsize=None)
    def select(state, horizon, flavor):
        if not horizon:
            return None, 0.
        _, _, branches = context(state)
        best, net = None, 0.
        _, erased = select(state, horizon-1, flavor)
        for i, options in enumerate(branches):
            value = (1-rate)*erased - ASK - SEND
            for sign, interval in options.items():
                _, continue_value = select(advance(state, i, sign), horizon-1, flavor)
                value += rate * interval["probability"] * (interval[flavor]+continue_value)
            if value > net + TOL:
                best, net = i, value
        return best, net

    def capture(opening, truth, budget, lookahead, flavor, counterpart):
        @lru_cache(maxsize=None)
        def execute(state, left):
            prior, before, branches = context(state)
            if left == 0:
                return {"record":before, "proved":float(prior!="UNRESOLVED"), "cost":0., "questions":0.,
                        "sends":0., "bridge_replies":0.}
            query, _ = select(state, min(left, lookahead), flavor)
            if query is None:
                return execute(state, 0)
            actual = truth[query]
            sign = actual == 1
            branch = branches[query][sign]
            next_state = advance(state, query, sign)
            sent = counterpart == "mandatory" or rate*branch["record"]-SEND > TOL
            p = rate if sent else 0.
            landed = execute(next_state, left-1)
            erased = execute(state, left-1)
            score = {k:p*landed[k]+(1-p)*erased[k] for k in erased}
            score["cost"] += ASK+SEND*sent
            score["questions"] += 1.
            score["sends"] += sent
            score["bridge_replies"] += p*(branch["record"] < TOL)
            return score

        before, pts, branches = context(opening)
        score = execute(opening, budget)
        score["record_gain"] = score["record"] - pts
        score["proof_gain"] = score["proved"] - (before != "UNRESOLVED")
        score["net"] = score["record_gain"] - score["cost"]
        score["projected"] = select(opening, min(budget,lookahead), flavor)[1]
        return score

    return context, select, capture


def panel(config, tree, rate):
    menu = config["menu"]
    context, select, capture = fixture(menu, tree, rate)
    totals = {arm: Counter() for arm in ARMS}
    witness = {}
    extra = Counter()
    for world in config["worlds"]:
        truth = tuple(1 if option in r.a.accepted(menu, world["requirements"][ROLES.index(role)]) else -1
                      for role, option in QUERIES)
        for present in product((False,True), repeat=len(QUERIES)):
            opening = tuple(t if show else 0 for t, show in zip(truth,present,strict=True))
            for name, spec in ARMS.items():
                totals[name].update(capture(opening, truth, *spec))

            one, _ = select(opening, 1, "record")
            exact2, expected = select(opening, 2, "record")
            trained, _ = select(opening, 2, "learned")
            extra["openings"] += 1
            extra["two_exact_openings_where_one_stops"] += exact2 is not None and one is None
            extra["first_question_disagreements"] += exact2 != trained
            if exact2 is not None:
                before, _, choices = context(opening)
                options = choices[exact2]
                if max(branch["record"] for branch in options.values()) < TOL:
                    extra["two_exact_first_query_no_immediate_value_for_either_sign"] += 1
                    if world["id"] not in witness and before=="UNRESOLVED":
                        sign = truth[exact2]==1
                        next_state = advance(opening,exact2,sign)
                        q2, _ = select(next_state,1,"record")
                        if q2 is not None:
                            second_when_delivered = truth[q2]==1
                            final = advance(next_state,q2,second_when_delivered)
                            final_decision, _, _ = context(final)
                            if final_decision!="UNRESOLVED":
                                witness[world["id"]] = {
                                    "opening":get_log(opening), "first_query":QUERIES[exact2],
                                    "first_sign":sign, "second_query":QUERIES[q2],"second_sign":second_when_delivered,
                                    "first_projected_joint_value":expected,"proof_after_two_if_delivered":final_decision,
                                    "marks":{key:capture(opening,truth,*spec) for key,spec in ARMS.items()},
                                }
    assert extra["openings"] == 768
    assert totals["two_exact"]["projected"]+TOL >= totals["one_exact"]["projected"]
    return {"totals":totals,"public_policy_differences":extra,"bridge_witnesses":witness}


def run():
    config_path=r.BENCH/"case.json"
    tree_path=r.BENCH/"transfer-fit.json"
    config=E.read(config_path)
    tree=E.read(tree_path)["tree"]
    paths=(Path(__file__), HERE/"protocol.md", HERE.parent/"route.py", config_path, tree_path)
    return {"mandatory_sign_cost":SEND,"question_cost":ASK,
            "results":{str(rate):panel(config,tree,rate) for rate in r.RATES},
            "sha256":{p.name:sha256(p.read_bytes()).hexdigest() for p in paths}}


if __name__=="__main__":
    E.emit(run())
