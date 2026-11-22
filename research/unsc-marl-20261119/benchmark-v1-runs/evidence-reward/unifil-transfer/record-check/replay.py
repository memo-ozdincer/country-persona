"""Render and score public-record witnesses from the held UNIFIL transfer."""
import argparse
from hashlib import sha256
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
BENCH = HERE.parent
sys.path.insert(0, str(BENCH))
import audit as a
import transfer_fit as trained

E = a.E
LABELS = ("costly_partial_impasse", "unnecessary_sign", "after_proof_attribution", "multiple_options")
WORD_CAP = 195


def case_inputs(config, world):
    documents = E.read(BENCH / config["sources"]["retrospective_evidence"])["evidence"]
    names = config["roles"]
    role_packets = [[{"id": f"mandate-{i}", "text": f"{name}: " + " ".join(f"{k} = {v}." for k,v in card.items())}]
                    for i, (name, card) in enumerate(zip(names, world["requirements"], strict=True))]
    accepted = [a.accepted(config["menu"], card) for card in world["requirements"]]
    gold = sorted(accepted[0] & accepted[1]) or ["IMPASSE"]
    menu = "\n".join(f"{p['id']}: {p['cadence']} {p['format']} briefing." for p in config["menu"])
    docs = [{**x, "source": x["url"]} for x in documents if x["id"] in ("vote", "operative", "brazil", "china")]
    return {"id": "2695/" + world["id"], "track": "workshop", "roles": names, "owned": role_packets,
            "task": "Summarize the official vote and the distinct fictional briefing workshop. Use "
                    "Decision: A, B, C, D, IMPASSE or UNRESOLVED on the first line. Preserve the public evidence and mandate scope.",
            "public": docs + [{"id":"scope","text": config["scope"]}, {"id":"menu","text": menu}],
            "gold": gold, "word_cap": WORD_CAP, "rubric": E.read(HERE/"rubric.json")}


def select(config):
    fit = E.read(BENCH/"transfer-fit.json")["tree"]
    menu = config["menu"]
    results = {}
    for world in config["worlds"]:
        cards = world["requirements"]
        sets = [a.accepted(menu, req) for req in cards]
        choices = [(role, q, a.public.signed.claim(f"{i}/{q}", role, q in sets[i], q))
                   for i, role in enumerate(a.ROLES) for q in a.OPTIONS]
        for opening in a.subsets([c for _,_,c in choices]):
            before, before_score, prior = a.state(menu, opening)
            for role, queried, claim in choices:
                after_log = [*opening, {**claim, "id": "reply"}]
                after, after_score, post = a.state(menu, after_log)
                sign = bool(claim.get("accepts"))
                other = a.ROLES[1-a.ROLES.index(role)]
                x = (*a.public.features(opening, role, queried, 1., sign),
                     float(len(prior[role]) == 1), float(len(prior[other]) == 1), float(len(post[role]) == 1))
                predicted = trained.predict(fit, x)
                gain = after_score-before_score
                categories = []
                if after == "IMPASSE" and before == "UNRESOLVED" and gain == .8 and .04*predicted > a.SEND:
                    categories.append("costly_partial_impasse")
                if after == "IMPASSE" and gain == 0. and .8*predicted > a.SEND:
                    categories.append("unnecessary_sign")
                if before == after == "IMPASSE" and gain > 0:
                    categories.append("after_proof_attribution")
                if world["id"] == "multiple-agreements" and before == "UNRESOLVED" and after in "ACD":
                    categories.append("multiple_options")
                for category in categories:
                    witness_key = (world["id"], tuple(row["id"] for row in opening), role, queried)
                    item = (witness_key, world, opening, after_log, predicted, gain)
                    if category not in results or witness_key < results[category][0]:
                        results[category] = item
    assert set(results) == set(LABELS)
    return results


def render(packet, menu, signs):
    blocks = E.judge.by_id(packet["public"])
    names = dict(zip(a.ROLES, packet["roles"], strict=True))
    names = {role: name.removesuffix(" workshop delegate") for role,name in names.items()}
    history = " ".join(blocks[k]["text"] for k in ("vote","operative","brazil","china"))
    decision, _, candidates = a.state(menu, signs)
    clauses = []
    if decision != "UNRESOLVED":
        for role, name in names.items():
            known = candidates[role]
            if len(known) == 1:
                (key, value), = known[0].items()
                clauses.append(f"{name}'s inferred workshop requirement is {key} {value}.")
            else:
                clauses.append(f"{name}'s full workshop requirement remains ambiguous.")
    if decision == "IMPASSE":
        proof = a.public.signed.chair.readout(a.OPTIONS, a.ROLES, signs)
        for role, name in names.items():
            rejected = [label for label, by_role in proof["blocked_options"].items() if role in by_role]
            if rejected:
                clauses.append(f"{name} excludes {', '.join(rejected)}.")
        clauses.append("The signed exclusions cover every option.")
    elif decision == "UNRESOLVED":
        clauses.append("The received signs do not certify an agreement or an impasse.")
    else:
        package = next(row for row in menu if row["id"] == decision)
        clauses.append(f"The signs support package {decision}, a {package['cadence']} {package['format']} briefing.")
    answer = f"Decision: {decision}\n\nHistorical record. {history}\n\nFictional workshop. {' '.join(clauses)}"
    answer += "\n\nThe workshop changes no mandate and grants no authority."
    assert len(answer.split()) <= packet["word_cap"], len(answer.split())
    return answer


def prepare():
    config = E.read(BENCH / "case.json")
    records, cases, deck = {}, {}, {}
    for category, (_, world, before, after, pred, gain) in select(config).items():
        case = case_inputs(config, world)
        public = {k:case[k] for k in ("roles","public","word_cap")}
        cases[category] = {}
        idmap = {}
        for horizon, log in (("before",before),("after",after)):
            text = render(public, config["menu"], log)
            names = dict(zip(a.ROLES, case["roles"], strict=True))
            log_text = " ".join(f"{names[row['role']]} {'accepts' if row.get('accepts') else 'excludes'} "
                                f"{(row.get('accepts') or row['excludes'])[0]}." for row in log)
            evidence = {"id": "public-signs", "text": log_text or "No signs have been delivered."}
            judging_case = case | {"public": [*case["public"], evidence]}
            cases[category][horizon] = judging_case
            pkt = E.final_packet(judging_case, [{},{},{"text":text}])
            idmap[horizon] = pkt["id"]
            deck[pkt["id"]] = pkt
        records[category] = {"world":world["id"], "before":before, "after":after, "proof_path": idmap,
                             "expected_proxy_gain":gain, "tree_predicted_gain":pred}
    return records, cases, [deck[key] for key in sorted(deck)]


def score(records, cases, deck):
    marks = E.read(HERE/"marks.json")
    packets = E.judge.by_id(deck)
    assert marks.keys() == packets.keys()
    results = {}
    for category, item in records.items():
        outcomes = {}
        for label, pid in item["proof_path"].items():
            calls = [{},{},{"text":packets[pid]["answer"],"termination":"complete"}]
            outcomes[label] = E.final_score(cases[category][label], calls, marks[pid])
        observed = (outcomes["after"]["released_70"] - outcomes["before"]["released_70"])/70
        results[category] = {"scores":outcomes, "normalized_released_gain":observed,
                             "proxy_gain":item["expected_proxy_gain"], "tree_predicted_gain":item["tree_predicted_gain"],
                             "net_at_04": .04*observed-a.SEND, "net_at_80": .80*observed-a.SEND}
    return {"unique_finals":len(deck),"results":results}


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("mode", choices=("replay","deck","score"))
    mode = cli.parse_args().mode
    records, cases, deck = prepare()
    E.emit(records if mode == "replay" else deck if mode == "deck" else score(records,cases,deck))
