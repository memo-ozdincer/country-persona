"""Stress-test bounded evidence logic and route the archived document cases."""
from collections import Counter
from hashlib import sha256
from itertools import product
import json
from pathlib import Path

import facilitator_scope_check_score as previous
from facilitator_scope_rules import CONFLICT, OPEN, inspect

HERE = previous.study.HERE
SCOPE = HERE / "facilitator-scope-check-evidence/results.json"


def quantify(size, covered, force):
    if force == "all":
        return covered == size
    if force == "some":
        return covered > 0
    if force == "none":
        return covered == 0
    if force == "not_all":
        return covered < size
    return 0 < covered < size


def controls():
    expressions = {"all": "addressed all of", "some": "addressed some of", "none": "addressed none of",
                   "not_all": "did not fully address", "part": "addressed some but not all of"}
    for a, b in product(expressions, repeat=2):
        statement = f"Delegate A said the text {expressions[a]} State B's concerns."
        witness = f"Delegate A said the text {expressions[b]} State B's concerns."
        overlap = any(quantify(3, n, a) and quantify(3, n, b) for n in range(4))
        yield f"coverage/{a}/{b}", statement, witness, f"{witness} A later paragraph concerns a separate vote.", OPEN if overlap else CONFLICT
    acts = ("voted in favor of", "voted against", "abstained on")
    for i, j in product(range(3), repeat=2):
        assertion = f"Delegate A {acts[i]} resolution 100 (2025)."
        witness = f"Delegate A {acts[j]} resolution 100 (2025)."
        yield f"vote/{i}/{j}", assertion, witness, witness, OPEN if i == j else CONFLICT
    assertion = "Delegate A voted in favour of resolution 100 (2025)."
    quoted = "Delegate A abstained on resolution 100 (2025)"
    guards = (
        ("transferred_actor", "Delegate B abstained on resolution 100 (2025).",
         "Delegate B abstained on resolution 100 (2025)."),
        ("different_year", "Delegate A abstained on resolution 100 (2024).",
         "Delegate A abstained on resolution 100 (2024)."),
        ("conditional_vote", quoted, f"{quoted} only in a mock session."),
        ("reported_speech", quoted, f"Delegate B falsely reported that {quoted}."),
        ("not_a_source_quote", quoted, "Delegate A voted in favour of resolution 100 (2025)."),
        ("duplicate_witness", quoted, f"{quoted}. {quoted}."),
        ("insufficient_fragment", "Delegate A", f"{quoted}."),
        ("hypothetical_context", quoted, f"A hypothetical example follows. {quoted}."),
        ("different_topic", "Delegate A said the text addressed none of State C's concerns.",
         "Delegate A said the text addressed none of State C's concerns."),
        ("pronoun_attribution", "It abstained on resolution 100 (2025).", "It abstained on resolution 100 (2025)."),
        ("unresolved_procedure", "Delegate A said the issue was discussed.", "Delegate A said the issue was discussed."),
    )
    for key, span, doc in guards:
        claim = "Delegate A said the text addressed some of State B's concerns." if key == "different_topic" else assertion
        yield f"scope_guard/{key}", claim, span, doc, None
    partial = "Delegate A said the text did not fully address State B's concerns."
    yield ("coverage/full_paraphrase", "Delegate A said the text fully addressed State B's concerns.",
           partial, partial, CONFLICT)


def evaluate_controls():
    records = {}
    for key, assertion, witness, source, expected in controls():
        result = inspect(assertion, witness, source)
        got = result["decision"] if result else None
        assert got == expected, (key, got, expected)
        records[key] = {"assertion": assertion, "witness": witness, "source": source,
                        "expected": expected, "result": result}
    return records


def rewritten(audit, strict):
    decisions = {}
    for key, old in audit.items():
        row = old["inputs"]
        check = inspect(row["assertion"], row["cited_words"], row["official_card"])
        # The fallback is the previously admitted contradiction, not the
        # failed learned compatibility check.
        admitted = check["decision"] if check else (OPEN if strict else CONFLICT)
        decisions[key] = {"admitted": admitted, "expected": old["expected"], "rule_result": check}
    return decisions


def replay(audited):
    writer = previous.study.base.load(previous.WRITER)["records"]["assertion"]
    return previous.replay(previous.receipt_bank(previous.ceiling.datasets(), audited, writer))


def corrected_headroom(audited):
    ceiling = previous.ceiling
    cohorts = ceiling.datasets()
    writer = previous.study.base.load(previous.WRITER)["records"]["assertion"]
    gate = previous.receipt_bank(cohorts, audited, writer)["unifil_colombia"]
    corrected = {(panel, ceiling.MODE): row for (panel, mode), row in gate.items() if mode == "checked"}
    frozen, independent = ceiling.stock()
    summary = {}
    for inventory in ("split", "overlap"):
        adaptive, max_adaptive = ceiling.solve(corrected, inventory, True)
        no_ack, max_independent = ceiling.solve(corrected, inventory, False)
        policy_set = (
            ("adaptive_ceiling", "learned", adaptive), ("independent_ceiling", "learned_erased", no_ack),
            ("frozen", "learned", frozen), ("trained_independent", "learned_erased", independent),
            ("greedy", "greedy", {}),
        )
        tested = ceiling.measure(corrected, policy_set, inventory)
        for k, upper in (("adaptive_ceiling", max_adaptive), ("independent_ceiling", max_independent)):
            assert abs(tested[k]["summary"][ceiling.MODE]["brief_net"] - upper["exact_net"]) < 1e-9
        summary[inventory] = {"ceilings": {"adaptive": max_adaptive, "independent": max_independent},
                              "policy_metrics": tested}
    return summary


def run():
    raw = previous.study.base.load(SCOPE)
    audit = raw["audit"]
    controls = evaluate_controls()
    variants = {}
    measured_headroom = None
    for name, strict in (("scoped_override", False), ("verified_only", True)):
        results = rewritten(audit, strict)
        live = {key: v for key, v in results.items() if not key.startswith("control/")}
        assert len(live) == 5
        counts = Counter()
        for value in live.values():
            counts["recognized"] += value["rule_result"] is not None
            counts["correct"] += value["admitted"] == value["expected"]
            counts["missed_conflict"] += value["expected"] == CONFLICT and value["admitted"] != CONFLICT
        variants[name] = {"routed_counts": counts, "decisions": results, "replay": replay(results)}
        if not strict:
            measured_headroom = corrected_headroom(results)
    return {"scope": "A bounded grammar checks literal source scope or a recorded vote for the same actor and referent. "
                     "The override retains prior contradictions outside its grammar. The verified-only arm drops those cases. "
                     "All official-record panels were previously used. Synthetic controls test the declared semantics.",
            "control_count": len(controls), "controls": controls, "variants": variants,
            "headroom_after_override": measured_headroom,
            "inputs_sha256": {p.name: sha256(p.read_bytes()).hexdigest() for p in
                              (Path(__file__), SCOPE, HERE / "facilitator_scope_rules.py", previous.WRITER)}}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, ensure_ascii=False))
