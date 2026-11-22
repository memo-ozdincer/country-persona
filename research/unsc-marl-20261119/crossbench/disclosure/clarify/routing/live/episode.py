"""Replayable role-local Qwen disclosures routed by the frozen policy."""
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))
from environment import claim, record, routing_prior, terminal
from guard import guarded
from joint import restore
from sanctions import project
from decision_ledger import readout

CAP = 56
CASES = (
    ("sanctions", "impasse", ("A", "C")),
    ("membership", "overlap", ("A", "B")),
    ("membership", "impasse", ("A", "E")),
)
ARMS = ("script", "learned")
SYSTEM = ("You are the named delegate in a fictional workshop. "
          "Answer only about the selected package under your own private instruction. "
          "A workshop preference is separate from the official record.")
TASK = ('Compare each exact required value against the selected package values. '
        'If every value matches, answer "accept". Otherwise answer "exclude". '
        'Return exactly one JSON object with keys "stance" and "option". '
        'Use the selected package ID. Do not replace or add packages.')


def source_paths():
    return {"sanctions":ROOT/"sanctions.json","membership":ROOT/"membership/case.json",
            "policy":ROOT/"evidence/joint/policy.json"}


def hashes():
    paths = {*source_paths().values(), HERE/"episode.py", HERE/"run.py",
             *(ROOT/n for n in ("environment.py","joint.py","guard.py","sanctions.py")),
             ROOT.parents[2]/"decision_ledger.py"}
    return {str(p.relative_to(ROOT.parents[2])):sha256(p.read_bytes()).hexdigest() for p in sorted(paths)}


def serialize(obj):
    return json.dumps(obj,ensure_ascii=False,separators=(",",":"))


def request(case, cards, role, letter, claims):
    option, = (x for x in case["options"] if x["id"]==letter)
    local = cards[role]
    user = {"delegate":case["roles"][role],"scope":case["boundary"],
            "historical_instrument":{k:case[k] for k in ("draft","meeting","date")},
            "historical_evidence":case["historical"],"public_disclosures":claims,
            "local_comparison":{"option":letter,"private_requirements":local,
                                "package_values":{k:option[k] for k in local}},
            "instruction":TASK}
    return [{"role":"system","content":SYSTEM},{"role":"user","content":serialize(user)}]


def judge(raw, role, letter, accepted, id_):
    def no_duplicates(pairs):
        d = dict(pairs)
        if len(d)!=len(pairs):
            raise ValueError("duplicate key")
        return d

    try:
        data = json.loads(raw,object_pairs_hook=no_duplicates)
    except (ValueError,TypeError):
        return "invalid_format",None
    if not isinstance(data,dict) or set(data)!={"option","stance"} or data["stance"] not in ("accept","exclude"):
        return "invalid_format",None
    if data["option"]!=letter:
        return "off_option",None
    if (data["stance"]=="accept") != accepted:
        return "untruthful",None
    return "admitted",{"id":id_,"role":role,"accepts":[letter] if accepted else [],
                       "excludes":[] if accepted else [letter]}


def episode(generate):
    """Generate deduplicated prompts, validate replies, and route only admitted evidence."""
    src = source_paths()
    docs = {k:json.loads(src[k].read_text()) for k in ("sanctions","membership")}
    choose = guarded(restore(json.loads(src["policy"].read_text())))
    sessions = {}
    for label,variant,open_ids in CASES:
        case = docs[label]
        roles, cards = case["roles"],case["variants"][variant]
        menu = [project(case["options"],c) for c in cards]
        assert bool(menu[0]&menu[1])==(variant=="overlap")
        letters = [r["id"] for r in case["options"]]
        same = {"case":case,"cards":cards,"menu":menu,"letters":letters,"open_ids":open_ids}
        assert all(mask & (1<<letters.index(option)) for mask,option in zip(menu,open_ids,strict=True))
        for arm in ARMS:
            sessions[label,variant,arm] = {**same,"role":1,"state":(0,0,0,0),"claims":[],"attempts":[]}

    used = {}
    for step in (-2,-1,*range(7)):
        pending, routes = {}, []
        for key, session in sessions.items():
            label,variant,arm = key
            case, cards, menu = (session[k] for k in ("case","cards","menu"))
            state, claims, letters = (session[k] for k in ("state","claims","letters"))
            full = (1<<len(letters))-1
            if step < 0:
                role = step+2
                letter = session["open_ids"][role]
                bit, next_role = 1<<letters.index(letter),1
                visible = []
            elif terminal(state,full):
                continue
            else:
                role = session["role"]
                local = menu[role]
                if arm=="script":
                    bit = claim(local,state,role,step,full,flex=True)
                    after = record(state,role,bit,bool(bit&local)) if bit else state
                    next_role = routing_prior(local,after,role,full) if bit else 1-role
                else:
                    _, actions, action = choose(menu,state,role,step,full)
                    bit, _, next_role = actions[action] if actions else (0,state,1-role)
                if not bit:
                    session["role"] = next_role
                    session["attempts"].append({"step":step,"role":role,"status":"pass"})
                    continue
                letter = letters[bit.bit_length()-1]
                visible = claims
            messages = request(case,cards,role,letter,visible)
            digest = sha256(serialize(messages).encode()).hexdigest()
            prompt = {"id":digest,"messages":messages,"cap":CAP}
            if digest not in used:
                pending[digest] = prompt
            routes.append((key,role,letter,bit,next_role,digest))

        if pending:
            fresh = generate(list(pending.values()))
            assert fresh.keys()==pending.keys()
            used.update(fresh)
        for key,role,letter,bit,next_role,digest in routes:
            session = sessions[key]
            admitted = bool(session["menu"][role]&bit)
            id_ = f"claim-{len(session['claims'])+1}"
            status,evidence = judge(used[digest]["output"],session["case"]["roles"][role],letter,admitted,id_)
            session["attempts"].append({"step":step,"role":role,"option":letter,"status":status,
                                        "response_id":digest,"admitted":evidence})
            if evidence:
                session["claims"].append(evidence)
                session["state"] = record(session["state"],role,bit,admitted)
            session["role"] = next_role if evidence or step<0 else 1-role

    result = {}
    for key,session in sessions.items():
        proof = readout(session["letters"],session["case"]["roles"],session["claims"])
        state = session["state"]
        assert bool(proof["state"]!="UNRESOLVED")==terminal(state,(1<<len(session["letters"]))-1)
        result["/".join(key)] = {"readout":proof,"claims":session["claims"],"attempts":session["attempts"],
                                 "admissions":dict(Counter(x["status"] for x in session["attempts"]))}
    return {"records":len(used),"episodes":result}
