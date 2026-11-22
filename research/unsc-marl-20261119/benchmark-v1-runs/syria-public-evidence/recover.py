"""Compare grounded clause recovery with strict reader-span admission."""
import json
import re

import admit
import reader

HERE, E = reader.HERE, reader.E


def clauses(text):
    return [s.strip() for s in re.split(
        r"(?<=[.!?])\s+|\n+|[,;]|\bconflicts? with\b|\bwhereas\b", text, flags=re.I) if s.strip()]


def author_clause(clause, speaker, field, value):
    """Require explicit ownership and binding force in the same local clause."""
    q = clause.lower()
    if not (re.search(admit.ROLE_NAMES[speaker], q) or re.search(r"\bmy\b", q)):
        return False
    if re.search(r"\b(?:reports? that|claims? that|says? that|according to)\b", q):
        return False
    return admit.pattern_ok(clause, speaker, field, value)


def correction(item, text, speaker, menu, scan):
    grounded = admit.admit(item, text, speaker, menu, True)
    quote_claim = admit.admit(item, text, speaker, menu, False).get("constraint")
    eligible = {}
    for clause in clauses(text):
        for field, value in admit.FIELD_PATTERNS:
            if author_clause(clause, speaker, field, value):
                eligible.setdefault((field, value), []).append(clause)
    grounded.pop("constraint", None)
    if len(eligible) != 1:
        return grounded
    (field, value), evidence = next(iter(eligible.items()))
    origins = [line for line in evidence if quote_claim and quote_claim["quote"] in line
               and (quote_claim["field"], quote_claim["value"]) == (field, value)]
    selected = evidence if scan else origins
    if selected:
        grounded["constraint"] = {"field": field, "value": value, "quote": selected[0]}
    return grounded


def run():
    raw = [json.loads(line) for line in (HERE / "evidence/extractions.jsonl").read_text().splitlines()]
    menu = next(iter(reader.baseline.roster().values()))["options"]
    original = E.read(HERE / "results.json")
    assert [r["request"] for r in raw] == reader.deck()
    scopes = {}
    for mode, scan in (("reader_clause", False), ("scan_clause", True)):
        found = {}
        for row in raw:
            req = row["request"]
            packet = json.loads(req["messages"][1]["content"])
            found[req["id"]] = correction(admit.decoded(row), packet["note"], packet["speaker"], menu, scan)
        scopes[mode] = found
    episodes = {}
    counts = {}
    for key, case, notes in reader.pair_inputs():
        row = original["episodes"][key]
        private = dict(zip(case["roles"], case["membership"], strict=True))
        compatible = {role: [p["id"] for p in menu if all(p[k] == v for k, v in card.items())]
                      for role, card in private.items()}
        out = {}
        for mode, selected in scopes.items():
            claims = [selected[reader.note_id(s, t)] for s, t in notes]
            msgs = admit.messages(claims, notes, menu)
            state = reader.review.ledger.readout(admit.OPTIONS, case["roles"], msgs)
            label = admit.exact(state)
            locally = [reader.review.ledger.truthful_disclosure(m, compatible[m["role"]]) for m in msgs]
            out[mode] = {"state": state, "decision": label, "evidence_supported": label in row["supported_by_archived_review"],
                         "workshop_correct": label in row["workshop_gold"], "claims": claims,
                         "all_claims_match_mandate": all(locally)}
        episodes[key] = out
    notes = {reader.note_id(s, t): (s, t, target) for s, t, target in reader.STRESS}
    for mode, scope in scopes.items():
        stress = {}
        for k, (_, _, target) in notes.items():
            hit = scope[k].get("constraint")
            stress[k] = ((hit["field"], hit["value"]) if hit else None) == target
        rows = [row[mode] for row in episodes.values()]
        counts[mode] = {"evidence_supported": sum(q["evidence_supported"] for q in rows),
                        "workshop_correct": sum(q["workshop_correct"] for q in rows),
                        "all_claims_match_mandate": sum(q["all_claims_match_mandate"] for q in rows),
                        "stress_correct": sum(stress.values()), "stress_rows": stress}
    negated = "The UK's fictional constraint does not mandate an additional checkpoint."
    extraction = {"constraint": {"field": "checkpoint", "value": "additional",
                                 "quote": "mandate an additional checkpoint"}, "endorsement": None}
    assert admit.admit(extraction, negated, reader.UK, menu, False)
    assert not correction(extraction, negated, reader.UK, menu, False)
    assert not correction(extraction, negated, reader.UK, menu, True)
    return {"summary": counts, "episodes": episodes, "admitted": scopes,
            "negation_probe_rejected": True,
            "prior_results_sha256": reader.baseline.sha(HERE / "results.json")}


if __name__ == "__main__":
    E.emit(run())
