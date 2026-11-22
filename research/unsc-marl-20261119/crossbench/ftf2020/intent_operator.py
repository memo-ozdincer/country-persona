"""Check request operators independently of archive-card lookup."""
import argparse
from itertools import batched
import json
from pathlib import Path
from unittest.mock import patch

import semantic_intent as semantic

partner = semantic.partner
HERE = semantic.HERE
MODES = {
    "one": "Exactly one specified record is requested. Background, an excluded item, or an item already held does not count.",
    "all": "The requester asks for each of several distinct records.",
    "any": "The requester explicitly authorizes one choice from two or more distinct alternative records.",
    "unspecified": "The request fails to identify which record it wants. A person's name or a topic alone may leave several possible records.",
}
ORDERS = (tuple(MODES), ("all", "unspecified", "one", "any"))
GUIDE = (
    "Decide what the assignment itself asks to retrieve, independently of which archival card might match it. "
    "Distinguish one specified record, a request for every listed record, an explicit choice among alternatives, "
    "and an unspecified request. Count requested records rather than mentions. Return only one choice letter."
)


def requests():
    for name, (wording, _, _) in semantic.examples().items():
        for i, order in enumerate(ORDERS):
            yield partner.replay.request(f"{name}/{i}", 4, GUIDE,
                                         {"assignment": wording,
                                          "choices": dict(zip("ABCD", (MODES[k] for k in order), strict=True))}, [])


def episode(generate):
    rows = {}
    for group in batched(requests(), 8):
        rows.update(generate(list(group)))
    return [{"family": "written-vote-intent-operator", "final": rows}]


def locks():
    return {**semantic.locks(), "operator": partner.digest(Path(__file__)),
            "semantic_decisions": partner.digest(HERE / "semantic-intent-evidence/results.json")}


def run(directory):
    with patch.object(partner.runner, "episode", episode), patch.object(partner.runner, "locks", locks):
        partner.runner.run(Path(partner.read(partner.writer.MODEL)["model"]), directory)


def prediction(row, order):
    return order[ord(row["output"]) - ord("A")] if row["ended"] and row["output"] in tuple("ABCD") else None


def report(directory):
    with patch.object(partner.replay, "episode", episode), patch.object(partner.replay, "locks", locks):
        rows = partner.replay.verify(directory)
    first = partner.read(HERE / "intent-evidence/results.json")["records"]
    stable = partner.read(HERE / "semantic-intent-evidence/results.json")["records"]
    result = {}
    for name, (text, truth, targets) in semantic.examples().items():
        labels = [prediction(rows[f"{name}/{i}"], order) for i, order in enumerate(ORDERS)]
        agreed = labels[0] if labels[0] == labels[1] else None
        observed = {method: source[name]["consensus"] for method, source in (("letters", first), ("semantic_ids", stable))
                    if name in source}
        gated = {}
        for key, value in observed.items():
            gate = value if value is not None and agreed == value[0] else None
            gated[key] = {"ungated": value, "gated": gate}
        result[name] = {"assignment": text, "reference": [truth, sorted(targets)],
                        "predictions": labels, "consensus_operator": agreed,
                        "operator_correct": agreed == truth, "decoders": gated}
    return {"scope": "An independent operator pass sees no archive-card choices. Verify the archived decoder's "
                     "operator before dispatch, and withhold on disagreement. No operator or archival IDs are "
                     "rewritten in this intervention.",
            "trace_sha256": partner.digest(directory / "transcript.jsonl"), "records": result}


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("mode", choices=("run", "score"))
    cli.add_argument("directory", type=Path)
    args = cli.parse_args()
    if args.mode == "run":
        run(args.directory)
    else:
        print(json.dumps(report(args.directory), ensure_ascii=False, indent=2))
