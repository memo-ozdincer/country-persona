"""Replay frozen extract policies through the actual DRC writer."""
from collections import defaultdict
import json
from pathlib import Path

import payload_policy as protocol
import payload_policy_writer as writer
from private_deliberation_score import RUBRIC
from private_payload_score import checked

HERE = Path(__file__).resolve().parent
POLICY = HERE / "evidence/payload-policy.json"
REVIEW = HERE / "payload-policy-review.json"
FACT_SOURCE = {
    "mandate_expiry": "mandate", "review_deadline": "review", "future_action": "review",
    "midterm_date": "reports", "final_date": "reports", "report_recipient": "reports",
    "committee_consultation": "reports", "committee_cadence": "updates",
}


def terminal(rows):
    review = writer.interface.parent.read(REVIEW)
    assert review["transcript_sha256"] == writer.runner.digest(writer.EVIDENCE / "transcript.jsonl")
    assert review["records"].keys() == rows.keys()
    assert FACT_SOURCE.keys() == RUBRIC["drc"].keys()
    results = {}
    for identifier, row in rows.items():
        held = frozenset(writer.SOURCE_IDS.index(key) for key in row["seen"])
        annotation = review["records"][identifier]
        observed = checked(annotation, row["output"], RUBRIC["drc"])
        licensed = {fact for fact, key in FACT_SOURCE.items() if writer.SOURCE_IDS.index(key) in held}
        supported = observed & licensed
        exact_fields = {key for key in row["seen"]
                        if {fact for fact, origin in FACT_SOURCE.items() if origin == key} <= supported}
        words = len(row["output"].split())
        results[held] = {"licensed": len(licensed), "facts": sorted(supported), "unlicensed": sorted(observed - licensed),
                         "exact_fields": sorted(exact_fields), "conflicts": annotation["conflicts"],
                         "safe_complete": not annotation["conflicts"] and not (observed - licensed)
                                          and row["ended"] and words <= 73,
                         "words": words, "output_tokens": len(row["output_ids"]), "ended": row["ended"]}
    return results


def generated(weights, focus, prior, peer, table):
    out = defaultdict(float)
    for (own, other), p in prior.items():
        for left, a in protocol.choose_probability(weights, "sender", focus, own):
            for seen, chance in ((None, 1 - peer), (left, peer)):
                if not a or not chance:
                    continue
                for right, b in protocol.choose_probability(weights, "recipient", focus, other, seen):
                    for held, delivered in protocol.delivery(left, right):
                        weight = p * a * chance * b * delivered
                        score = table[held]
                        out["mass"] += weight
                        out["licensed_fact_count"] += weight * score["licensed"]
                        out["preserved_facts_out_of_8"] += weight * len(score["facts"])
                        out["safe_completed_rate"] += weight * score["safe_complete"]
                        out["safe_preserved_facts"] += weight * len(score["facts"]) * score["safe_complete"]
                        out["expected_writer_output_tokens"] += weight * score["output_tokens"]
                        actual = {writer.SOURCE_IDS.index(key) for key in score["exact_fields"]}
                        out["both_publicly_requested_fields_preserved"] += weight * (set(focus) <= actual)
                        out["preserved_field_reward"] += weight * protocol.value(actual, focus)
    assert abs(out.pop("mass") - 1) < 1e-9
    out["preserved_field_net"] = out["preserved_field_reward"] - (protocol.PEER_FEE if peer else 0.)
    return dict(out)


def run():
    raw, _ = writer.replay(writer.EVIDENCE)
    table = terminal(raw)
    fit = writer.interface.parent.read(POLICY)
    assert fit["pins"]["payload_policy.py"] == writer.runner.digest(Path(protocol.__file__))
    def immutable(obj):
        return tuple(map(immutable, obj)) if isinstance(obj, list) else obj
    learned = {immutable(row["state"]): row["probabilities"] for row in fit["policy"]}
    regimes = {}
    for label in ("training", "overlap", "split"):
        prior = protocol.roster(label)
        rows = []
        for focus in protocol.PAIRS:
            _, opt = protocol.best_script(focus, prior, protocol.PEER)
            _, independent = protocol.best_script(focus, prior, 0.)
            options = {
                "learned": (learned, protocol.PEER),
                "learned_no_peer": (learned, 0.),
                "greedy": (protocol.greedy(focus), protocol.PEER),
                "best_independent": (independent, 0.),
                "optimized_interactive": (opt, protocol.PEER),
            }
            rows.append({"focus": [writer.SOURCE_IDS[i] for i in focus],
                         "metrics": {name: generated(weights, focus, prior, peer, table)
                                     for name, (weights, peer) in options.items()}})
        regimes[label] = {"rows": rows, "mean": {
            name: {k: float(sum(row["metrics"][name][k] for row in rows) / len(rows)) for k in metrics}
            for name, metrics in rows[0]["metrics"].items()}}
    return {"scope": "Same-assistant exact-span review of frozen Qwen outputs on the DRC docket. Policies and scripts "
                     "optimize the original typed delivery endpoint. No target prose score informs route selection. "
                     "Both the source holders and message loss are simulated.",
            "terminal_sets": {",".join(writer.SOURCE_IDS[i] for i in sorted(held)) or "public": values
                              for held, values in table.items()},
            "inventories": regimes, "pins": {p.name: writer.runner.digest(p) for p in (
                POLICY, REVIEW, Path(__file__), writer.EVIDENCE / "transcript.jsonl")}}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
