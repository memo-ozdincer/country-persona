"""Replay exact-quote request decisions and audit the lexical gate's boundary."""
from hashlib import sha256
from itertools import product
import json
from pathlib import Path

import request_witness as witness
import scoped_relay as relay

HERE = witness.HERE
FOILS = {
    "missing_required_member": ("Retrieve both the United States' explanation and Russia's explanation.",
                                "the United States' explanation", False),
    "outside_exclusion": ("Retrieve Russia's explanation rather than the United States' explanation.",
                          "the United States' explanation", False),
    "inside_sentence_negation": ("Do not get the United States' explanation. Get Russia's explanation.",
                                 "the United States' explanation", False),
    "previously_held": ("I already have Russia's explanation. Get the United States' explanation.",
                        "Russia's explanation", False),
    "no_requested_acts": ("Djani and the vote appear on this file. Find the relevant records.", "Djani", False),
    "two_explicit_targets": ("Retrieve both the United States' explanation and Russia's explanation.",
                             "the United States' explanation\nRussia's explanation.", True),
}


def run():
    path = HERE / "witness-evidence/results.json"
    cases = relay.archive.read(path)["records"]
    estimator = relay.binary.decoder.transfer.Calibration()
    comparisons = {
        "letters": relay.archive.read(HERE / "intent-evidence/results.json")["records"],
        "semantic_ids": relay.archive.read(HERE / "semantic-intent-evidence/results.json")["records"],
    }
    overlap = {}
    for method, archive in comparisons.items():
        shared = [(value, cases[key]) for key, value in archive.items()]
        overlap[method] = {"examples": len(shared), "prior_exact": sum(a["exact"] for a, _ in shared),
                           "witness_exact": sum(b["exact"] for _, b in shared),
                           "witness_wrong_dispatch": sum(b["wrong_dispatch"] for _, b in shared)}
    modes = {}
    for name, case in cases.items():
        expected, decoded = case["reference"], case["decision"]
        scores = {}
        for method, value in (("model", decoded), ("typed", expected)):
            branches = [(q, r, relay.named(value, focus, roster, q, r))
                        for focus, roster, q, r in product(range(4), relay.archive.PAIRS, (0, 1), (0, 1))]
            scores[method] = relay.total(expected, branches, estimator.question_loss, estimator.reply_loss)
        modes[name] = {"kind": expected[0], "scores": scores}
    summary = {}
    for kind in ("one", "all", "any", "unspecified"):
        group = [value["scores"] for value in modes.values() if value["kind"] == kind]
        summary[kind] = {arm: {metric: sum(row[arm][metric] for row in group) / len(group)
                               for metric in group[0][arm]}
                         for arm in ("model", "typed")}
    foils = {}
    for label, (text, spans, admissible) in FOILS.items():
        decoded, explanation = witness.compile_intent(text, spans, True)
        admitted = bool(decoded and decoded[0] != "unspecified")
        foils[label] = {"text": text, "synthetic_proposed_spans": spans, "intended_admission": admissible,
                        "admitted": admitted, "returned": decoded, "reason": explanation}
    return {"scope": "Same one-reply relay and uniform authenticated inventories as the earlier intent comparison. "
                     "The lexical foils substitute proposed quote spans directly and do not represent model outputs.",
            "code_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
            "witness_sha256": sha256(path.read_bytes()).hexdigest(), "overlap": overlap,
            "replay_summary": summary, "case_metrics": modes, "lexical_boundary_checks": foils}


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, indent=2))
