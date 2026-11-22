"""Judge the relationship directly from a documentary witness and a claim."""
import argparse
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
from unittest.mock import patch

import facilitator_entailment as prior

HERE = prior.HERE
runner = prior.runner
protocol = prior.protocol
LABELS = ("supports", "contradicts", "unknown")
OPTIONS = (
    "The cited wording establishes the exact assertion.",
    "The cited wording makes the assertion impossible as stated.",
    "The cited wording leaves the assertion unresolved.",
)
TASK = (
    "Read the quoted words as the premise. Use the full passage to resolve the speaker, referents and the "
    "act under discussion. Compare the premise with the assertion as written. "
    "To establish it, the cited words must cover the actor, act and qualifications. "
    "To rule it out, the cited words and the assertion must be incompatible. If the assertion could be true "
    "or false given those words, choose unresolved. Distinguish legal authorization, political endorsement, "
    "and the casting of a vote. A statement about one body cannot establish another body's position."
)
# Each contrast reuses an exact witness from a routed case. These rows never
# enter the router or its training mixture.
CONTROLS = (
    ("partial/not_every", "unifil/1/1", "China said the text did not address every concern Lebanon raised.", "supports"),
    ("partial/none", "unifil/1/1", "China said the text addressed none of Lebanon's concerns.", "unknown"),
    ("vote/endorsement", "haiti/1/1", "The three African members supported adoption under Chapter VII.", "supports"),
    ("vote/opposition", "haiti/1/1", "The three African members opposed adoption under Chapter VII.", "contradicts"),
    ("abstention/no_vote", "haiti/1/0", "China cast neither an affirmative nor a negative vote on the authorization.", "supports"),
    ("abstention/negative_vote", "haiti/1/0", "China cast a negative vote on the authorization.", "contradicts"),
    ("actor/brazil", "unifil/0/1", "Brazil supported UNIFIL's continued work.", "unknown"),
    ("condition/satisfied", "colombia/1/1", "The three African members stated that the Secretary-General's conditions were already met.", "unknown"),
)


def fixtures():
    archived = protocol.delivery.load(prior.routing.ARTIFACT)["reads"]
    inputs = {}
    for key, previous, _ in prior.fixtures():
        payload = {"quoted_premise": previous["highlighted_quote"],
                   "passage_for_references": previous["source_context"], "assertion": previous["claim"]}
        inputs[key] = payload
        yield "routed", key, payload, archived[key]["expected"]
    for key, base, assertion, expected in CONTROLS:
        yield "control", key, inputs[base] | {"assertion": assertion}, expected


def prompts():
    for group, key, payload, _ in fixtures():
        yield from protocol.encoded((group, key), TASK, payload, OPTIONS)


def pins():
    path = Path(__file__).resolve()
    return prior.pins() | {str(path.relative_to(HERE.parents[1])): sha256(path.read_bytes()).hexdigest()}


def score(directory):
    with patch.multiple(runner, observations=prompts, hashes=pins):
        rows = runner.read(directory)
    archived = protocol.delivery.load(prior.routing.ARTIFACT)["reads"]
    previous = {key: row["admitted"] for key, row in archived.items()}
    agreement_gate = dict.fromkeys(previous, "unknown")
    direct_relation = agreement_gate.copy()
    totals = {}
    decisions = {}
    for group, key, payload, expected in fixtures():
        labels = protocol.votes(rows, (group, key), LABELS)
        chosen = protocol.stable(labels) or "unknown"
        counts = totals.setdefault(group, Counter())
        counts["total"] += 1
        counts["correct"] += chosen == expected
        counts["wrong_actionable_relation"] += chosen != expected and chosen != "unknown"
        counts["valid_relation_withheld"] += chosen == "unknown" and expected != "unknown"
        counts["order_disagreement"] += labels[0] != labels[1]
        if expected == "contradicts":
            counts["true_contradictions"] += 1
            counts["true_contradictions_recovered"] += chosen == expected
        if group == "routed":
            direct_relation[key] = chosen
            if chosen == previous[key]:
                agreement_gate[key] = chosen
        decisions[f"{group}/{key}"] = {"assertion": payload["assertion"], "expected": expected,
                                      "votes": labels, "stable_relation": chosen}

    full_packets = {}
    base = prior.witness.transfer.base
    panels = prior.witness.transfer.PANELS
    for name, readings in (("quote_only", previous), ("source_relation_gate", agreement_gate),
                           ("source_relation_replace", direct_relation)):
        records = []
        for family, proposals in panels.items():
            for index, (proposal, _, truth) in enumerate(proposals):
                visible = tuple(readings[f"{family}/{index}/{pos}"] for pos in range(2))
                records.append({"proposal": proposal, "expected": base.decision(truth, base.TARGETS),
                                "action": base.decision(visible, base.TARGETS)})
        full_packets[name] = records
    replay = prior.routing.run({"source_relation_gate": agreement_gate, "source_relation_replace": direct_relation})
    return {"scope": "Frozen Qwen judges exact archived spans without seeing the previous relation. "
                     "Authored contrast rows never enter the router. Option-order disagreements resolve to unknown.",
            "summary": totals, "decisions": decisions, "full_packets": full_packets,
            "replay": replay["replay"], "source_sha256": replay["source_sha256"]}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("run", "score"))
    parser.add_argument("directory", type=Path)
    parser.add_argument("--model", type=Path)
    args = parser.parse_args()
    if args.mode == "run":
        with patch.multiple(runner, observations=prompts, hashes=pins):
            runner.score(args.model, args.directory)
    else:
        print(json.dumps(score(args.directory), indent=2))
