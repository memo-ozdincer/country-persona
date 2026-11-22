"""Typed public messages for a two-round language actor baseline."""
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))
from decision_ledger import readout, truthful_disclosure
from packets import inputs, packet

FAMILY = "iraq-unami-mandate-review-2023"
CAP = 64
SYSTEM = (
    "You are one simulated delegate in a fictional post-vote workshop. "
    "Use only your private condition and the supplied package descriptions. "
    "Historical votes establish no new workshop commitment. "
    "The group gets credit for a verified compatible option or verified impasse. "
    "A compatible option requires both roles to disclose that they can accept it. "
    "An impasse needs at least one exclusion for every package."
)
FORMAT = (
    'Return only one JSON object with exactly two list fields, "accepts" and "excludes". '
    "Across both lists you may give at most one option ID from A, B, C, D. "
    'For example {"accepts":[],"excludes":["C"]} is one exclusion. '
    "Use two empty lists to pass. Report only truthful claims about your own private condition. "
    "Choose a claim that could help the group establish the outcome."
)


def serialize(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def family_inputs():
    data, refs = inputs()
    item = next(r for r in data["families"] if r["id"] == FAMILY)
    variants = item["variants"]
    views = {v["id"]: [packet(item, v, data["boundary"], f"role-{i}") for i in (1, 2)] for v in variants}
    for pair in views.values():
        for view in pair:
            del view["task"]
    assert views["overlap"][0] == views["impasse"][0]
    reference = refs["families"][FAMILY]["workshop_refs_only"]
    return item["roles"], views, reference


def admit(raw, record_id, author, known):
    """Return an environment-validated claim, keeping rejection classes distinct."""
    def no_duplicates(pairs):
        r = dict(pairs)
        if len(r) != len(pairs):
            raise ValueError("Repeated JSON key")
        return r

    try:
        msg = json.loads(raw, object_pairs_hook=no_duplicates)
        if not isinstance(msg, dict) or set(msg) != {"accepts", "excludes"}:
            raise ValueError("Expected accepts and excludes lists")
        if not all(isinstance(msg[v], list) and all(x in "ABCD" for x in msg[v] if isinstance(x, str))
                   and all(isinstance(x, str) and len(x) == 1 for x in msg[v]) for v in msg):
            raise ValueError("Expected one-letter option IDs")
        if len(msg["accepts"]) + len(msg["excludes"]) > 1:
            raise ValueError("Claim budget exceeded")
    except (ValueError, TypeError):
        return {"kind": "invalid_format", "admitted": None}
    if not truthful_disclosure(msg, known):
        return {"kind": "untruthful_claim", "admitted": None}
    if not msg["accepts"] and not msg["excludes"]:
        return {"kind": "pass", "admitted": None}
    return {"kind": "disclosure", "admitted": {"id": record_id, "role": author, **msg}}


def request(id_, view, own=None, other=None, second=False, peer_visible=False):
    message = {"role_view": view, "task": FORMAT}
    if second:
        message["own_preceding_admitted_disclosure"] = own
        if peer_visible:
            message["peer_preceding_admitted_disclosure"] = other
            message["task"] += " The peer field is its actual admitted first disclosure, or null if none. Do not repeat your own earlier claim."
        else:
            message["task"] += " Review independently without a peer turn. Do not repeat your own earlier claim."
    else:
        message["task"] += " This is your opening disclosure. No peer turn has been seen."
    return {"id": id_, "cap": CAP, "messages": [{"role": "system", "content": SYSTEM},
            {"role": "user", "content": serialize(message)}]}


def summarize(roles, ref, turns):
    admitted = [x["judgment"]["admitted"] for x in turns if x["judgment"]["admitted"]]
    result = readout("ABCD", roles, admitted)
    observed = {role: set() for role in roles}
    repeats = 0
    for claim in admitted:
        signatures = {(kind, option) for kind in ("accepts", "excludes") for option in claim[kind]}
        repeats += len(signatures & observed[claim["role"]])
        observed[claim["role"]].update(signatures)
    target = ref["joint_packages"]
    verified = list(result["verified_options"])
    correct = bool(verified) and set(verified) <= set(target) if target else result["state"] == "IMPASSE"
    return {"readout": result, "target_compatible": target, "correct": correct,
            "distinct_valid_claims": sum(map(len, observed.values())), "repeated_claims": repeats,
            "invalid_format": sum(t["judgment"]["kind"] == "invalid_format" for t in turns),
            "untruthful_claims": sum(t["judgment"]["kind"] == "untruthful_claim" for t in turns),
            "passes": sum(t["judgment"]["kind"] == "pass" for t in turns),
            "clean_correct": correct and all(t["judgment"]["kind"] not in {"invalid_format", "untruthful_claim"}
                                                for t in turns)}


def script(roles, reference, mode):
    """Controls use only signed local facts and, for the probe, public history."""
    turns = []
    last = [None, None]
    for rnd in (0, 1):
        received = last.copy()
        for i, (role, menu) in enumerate(zip(roles, reference["allowed_by_role"], strict=True)):
            positive = mode == "support_first"
            if mode == "public_A_probe":
                positive = (i == 1 and "A" in menu) or (rnd == 1 and received[1-i] is not None
                      and bool(received[1-i]["accepts"]) and received[1-i]["accepts"][0] in menu)
            key, options = ("accepts", sorted(menu)) if positive else ("excludes", sorted(set("ABCD") - set(menu)))
            already = last[i][key] if last[i] else []
            viable = [o for o in options if o not in already]
            if mode == "public_A_probe" and positive and rnd == 1 and received[1-i] and received[1-i]["accepts"]:
                matching = received[1-i]["accepts"][0]
                if matching in viable:
                    viable = [matching] + [o for o in viable if o != matching]
            content = {"accepts": [], "excludes": []}
            content[key] = viable[:1]
            judgment = admit(serialize(content), f"script-{rnd}-{i}", role, menu)
            turns.append({"judgment": judgment})
            last[i] = judgment["admitted"]
    return summarize(roles, reference, turns)
