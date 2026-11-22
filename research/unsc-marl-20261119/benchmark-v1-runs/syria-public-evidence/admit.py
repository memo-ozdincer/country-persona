"""Replay source-gated evidence extraction through the public decision ledger."""
from collections import Counter
import json
import re

import reader

HERE, E = reader.HERE, reader.E
OPTIONS = ("A", "B", "C", "D")
FIELD_PATTERNS = {
    ("duration", "nine"): r"\bnine[ -]months?\b|\bduration\s*=\s*nine\b",
    ("duration", "six"): r"\bsix[ -]months?\b|\bduration\s*=\s*six\b",
    ("checkpoint", "additional"): r"\b(?:additional|extra) (?:formal )?(?:review )?checkpoint\b|\bcheckpoint\s*=\s*additional\b",
}
ROLE_NAMES = {
    reader.BR: r"\bbrazil(?:ian)?\b",
    reader.UK: r"\b(?:uk|united kingdom)\b",
}
MODAL = r"\b(?:mandate\w*|require\w*|constraint\w*|binding|must|only)\b"
NEGATION = r"\b(?:not|never|no|nor|neither|cannot|can't|non.binding|optional|hypothetically|if)\b"
PROPOSAL = r"\b(?:propos\w*|recommend\w*|accept\w*|endorse\w*|support\w*)\b"


def decoded(row):
    if row["response"]["termination"] != "complete":
        return {}
    try:
        item = json.loads(row["response"]["text"])
    except ValueError:
        return {}
    return item if isinstance(item, dict) and item.keys() == {"constraint", "endorsement"} else {}


def pattern_ok(quote, speaker, field, value):
    q = quote.lower()
    if not re.search(FIELD_PATTERNS[(field, value)], q) or not re.search(MODAL, q):
        return False
    if re.search(NEGATION, q) or re.search(r"\b(?:histor|draft|vot)\w*", q):
        return False
    if len(re.split(r"[.!?]\s+", q)) > 1:
        return False
    return not any(re.search(pattern, q) for role, pattern in ROLE_NAMES.items() if role != speaker)


def endorsement_ok(quote, speaker, option, menu):
    q = quote.lower()
    if re.search(NEGATION, q) or not re.search(PROPOSAL, q):
        return False
    if any(re.search(p, q) for role, p in ROLE_NAMES.items() if role != speaker):
        return False
    letters = re.findall(r"\b(?:package|option)\s*[- ]?([a-d])\b", q)
    if letters:
        return set(letters) == {option.lower()}
    target, = [row for row in menu if row["id"] == option]
    oversight = r"\bordinary reporting\b" if target["checkpoint"] == "ordinary" else FIELD_PATTERNS[("checkpoint", "additional")]
    return bool(re.search(FIELD_PATTERNS[("duration", target["duration"])], q) and re.search(oversight, q))


def admit(item, text, speaker, menu, semantic):
    accepted = {}
    for kind, specification in (
        ("constraint", {"field", "value", "quote"}),
        ("endorsement", {"option", "quote"}),
    ):
        claim = item.get(kind)
        if not isinstance(claim, dict) or set(claim) != specification or not all(isinstance(v, str) for v in claim.values()):
            continue
        quote = claim["quote"]
        if not quote.strip() or quote not in text or len(quote.split()) > 32:
            continue
        # Check the containing sentence as well as the selected substring.
        # This keeps a substring from silently dropping a negation or attribution.
        contexts = [s for s in re.split(r"(?<=[.!?])\s+|\n+", text) if quote in s]
        if semantic and not contexts:
            continue
        spans = [quote, *contexts]
        if kind == "constraint":
            field, value = claim["field"], claim["value"]
            if (field, value) not in FIELD_PATTERNS or semantic and not all(
                    pattern_ok(span, speaker, field, value) for span in spans):
                continue
        else:
            option = claim["option"]
            if option not in OPTIONS or semantic and not all(
                    endorsement_ok(span, speaker, option, menu) for span in spans):
                continue
        accepted[kind] = claim
    return accepted


def messages(claims, notes, options):
    world = []
    for i, (claim, (speaker, _)) in enumerate(zip(claims, notes, strict=True)):
        if mandate := claim.get("constraint"):
            excludes = [row["id"] for row in options if row[mandate["field"]] != mandate["value"]]
            world.append({"id": f"{i}-mandate", "role": speaker, "excludes": excludes})
        if offered := claim.get("endorsement"):
            world.append({"id": f"{i}-offer", "role": speaker, "accepts": [offered["option"]]})
    return world


def exact(rows):
    if rows["state"] == "AGREEMENT_POSSIBLE":
        return sorted(rows["verified_options"])[0]
    return "I" if rows["state"] == "IMPASSE" else "U"


def run():
    raw = [json.loads(line) for line in (HERE / "evidence/extractions.jsonl").read_text().splitlines()]
    assert [r["request"] for r in raw] == reader.deck()
    menu = next(iter(reader.baseline.roster().values()))["options"]
    inputs = {r["request"]["id"]: json.loads(r["request"]["messages"][1]["content"]) for r in raw}
    outputs = {r["request"]["id"]: decoded(r) for r in raw}
    arms = {}
    for key, verify in (("quote_only", False), ("source_gate", True)):
        arms[key] = {k: admit(outputs[k], req["note"], req["speaker"], menu, verify) for k, req in inputs.items()}
    leader = E.read(HERE.parent / "workshop-joint-action-fit/calibration/balanced.json")["archived"]["actions"]
    episodes = {}
    for key, case, notes in reader.pair_inputs():
        gold = ["I" if p == "IMPASSE" else p for p in case["gold"]]
        reference = leader[key]
        assert reference["gold"] == gold
        output = {"supported_by_archived_review": reference["supported"], "workshop_gold": gold,
                  "balanced_joint_chair": reference["arms"]["joint_chair"]}
        for arm, accepted in arms.items():
            claims = [accepted[reader.note_id(s, t)] for s, t in notes]
            submitted = messages(claims, notes, menu)
            audit = [reader.review.ledger.truthful_disclosure(m, [
                row["id"] for row in menu if all(
                    row[k] == v for k, v in case["membership"][case["roles"].index(m["role"])].items())
            ]) for m in submitted]
            ledger = reader.review.ledger.readout(OPTIONS, case["roles"], submitted)
            decision = exact(ledger)
            output[arm] = {"ledger": ledger, "claims": claims, "truthful": audit, "decision": decision,
                           "matches_archived_support": decision in reference["supported"],
                           "workshop_correct": decision in gold, "source_safe": all(audit)}
        episodes[key] = output
    st = {}
    for speaker, sentence, goal in reader.STRESS:
        k = reader.note_id(speaker, sentence)
        st[k] = {"text": sentence, "expected": list(goal) if goal else None}
        for arm, rows in arms.items():
            selected = rows[k].get("constraint")
            actual = [selected["field"], selected["value"]] if selected else None
            st[k][arm] = {"admitted": actual, "correct": actual == st[k]["expected"]}
    aggregate = {arm: {
        "archived_evidence_supported": sum(row[arm]["matches_archived_support"] for row in episodes.values()),
        "archived_workshop_correct": sum(row[arm]["workshop_correct"] for row in episodes.values()),
        "archived_all_claims_match_mandate": sum(row[arm]["source_safe"] for row in episodes.values()),
        "stress_correct": sum(row[arm]["correct"] for row in st.values()),
        "accepted_constraints": sum("constraint" in q for q in rows.values()),
        "accepted_endorsements": sum("endorsement" in q for q in rows.values()),
    } for arm, rows in arms.items()}
    digest_files = ("extractions.jsonl", "reader-lock.json")
    return {"schema_valid": sum(bool(o) for o in outputs.values()), "calls": len(raw), "aggregate": aggregate,
            "episodes": episodes, "stress": st, "admitted": arms,
            "input_sha256": {f: reader.baseline.sha(HERE / "evidence" / f) for f in digest_files}}


if __name__ == "__main__":
    E.emit(run())
