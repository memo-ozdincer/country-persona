"""Check a specific quoted witness before forwarding its relation."""
import argparse
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
from unittest.mock import patch

import facilitator_witness as witness
import facilitator_witness_replay as routing

HERE = witness.HERE
protocol = witness.transfer.protocol
runner = witness.transfer.runner
LABELS = ("establishes_proposed_relation", "insufficient", "establishes_opposite_relation")
TASK = (
    "Audit a proposed relationship between a documentary quote and a claim. "
    "Option establishes_proposed_relation applies only if the highlighted quote establishes the proposed relation "
    "for the exact named party, action, and scope. Use the surrounding source only to resolve who and what "
    "the quote refers to. Check wording strength: a limit on all does not decide whether some, and support for "
    "adoption or discussion does not alone establish a vote, commitment, or a separate claim. "
    "A contradiction requires that the quoted position and the claim cannot both be true. "
    "Use insufficient for silence, incomplete coverage, or any remaining ambiguity. "
    "Use establishes_opposite_relation only when the quote establishes the other relation."
)


def fixtures():
    saved = protocol.delivery.load(routing.ARTIFACT)["reads"]
    for key, claim, source, truth in witness.cases():
        row = saved[key]
        relation, quote = row["admitted"], row["witness"]
        assert row["claim"] == claim and row["expected"] == truth
        if relation != "unknown":
            assert quote and quote in source
            yield key, {"claim": claim, "proposed_relation": relation, "highlighted_quote": quote,
                        "source_context": source}, relation == truth


def prompts():
    for key, payload, _ in fixtures():
        yield from protocol.encoded(("audit", key), TASK, payload, LABELS)


def pins():
    paths = (Path(__file__), Path(routing.__file__), routing.ARTIFACT, routing.TRANSFER,
             *(HERE.parents[1] / p for p in witness.hashes()))
    return {str(p.resolve().relative_to(HERE.parents[1])): sha256(p.read_bytes()).hexdigest() for p in paths}


def score(directory):
    with patch.multiple(runner, observations=prompts, hashes=pins):
        raw = runner.read(directory)
    decisions = {}
    audited = {}
    summary = {}
    for key, _, _ in witness.cases():
        decisions[key] = "unknown"
    for key, payload, expected in fixtures():
        labels = protocol.votes(raw, ("audit", key), LABELS)
        accept = protocol.stable(labels) == LABELS[0]
        if accept:
            decisions[key] = payload["proposed_relation"]
        family = key.split("/")[0]
        counts = summary.setdefault(family, Counter())
        counts["correct_admitted" if expected else "incorrect_admitted"] += 1
        counts["valid_pass" if accept and expected else "invalid_pass" if accept else
               "valid_veto" if expected else "invalid_veto"] += 1
        audited[key] = {"expected_accept": expected, "votes": labels, "accepted": accept,
                        "relation_after_gate": decisions[key]}
    scored = routing.run({"model_veto": decisions})
    return {"scope": "Same frozen model, separate claim-to-quote review and strict agreement across two option orders. "
                     "This gate can only remove candidate relations. The evaluation uses the existing authored labels.",
            "scored": summary, "audit": audited, "relations": decisions,
            "replay": scored["replay"], "source_sha256": scored["source_sha256"]}


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
