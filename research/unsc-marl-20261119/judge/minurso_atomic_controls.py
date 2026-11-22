"""Use a genuine omission and move all three answers through every letter."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import sys
from unittest.mock import patch

import minurso_atomic_judge as first
from minurso_atomic_review import digest, pick, read_model

ORDERS = ((0, 1, 2), (1, 2, 0), (2, 0, 1))
TARGETS = {
    "anchor-base": (*first.SELECTED, "tally"),
    "anchor-nonparticipation": ("nonparticipation", "tally"),
    "anchor-amendment": ("798-outcome", "798-content"),
    "anchor-capacity": ("capacity", "798-outcome"),
    "anchor-authority": ("no-monitoring", "798-outcome"),
    "anchor-approval-scope": ("798-content", "798-outcome"),
    "anchor-omitted": ("nonparticipation", "tally"),
}


def cases():
    fixtures = [(name, text.replace(", explaining its decision not to participate", ""), gold)
                for name, text, gold in first.fixtures()]
    omitted = next(text for name, text, _ in fixtures if name == "anchor-omitted")
    assert "participat" not in omitted.lower()
    for name, text, gold in fixtures:
        for part in TARGETS[name]:
            yield name, text, part, gold.get(part, 1)


def observations():
    _, parts = first.rubric()
    blocks = {r["id"]: r["text"] for r in json.loads(first.ANCHORS.read_text())[0]["packet"]["evidence"]}
    for name, text, criterion, _ in cases():
        part = parts[criterion]
        for i, order in enumerate(ORDERS):
            body = {"evidence": {k: blocks[k] for k in part["blocks"]}, "candidate": text,
                    "tested_fact": part["criterion"],
                    "choices": {k: first.OPTIONS[v] for k, v in zip("ABC", order, strict=True)}}
            yield {"observation": (name, criterion, i), "legal": order, "messages": [
                {"role": "system", "content": first.SYSTEM},
                {"role": "user", "content": json.dumps(body, ensure_ascii=False)},
            ]}


def hashes():
    path = Path(__file__).resolve()
    return {**first.hashes(), str(path.relative_to(first.ROOT)): digest(path)}


def run(model, directory):
    sys.path.insert(0, str(first.ROOT))
    import relay_text
    with patch.multiple(relay_text, observations=observations, hashes=hashes):
        relay_text.score(model, directory)


def report(directory):
    rows = read_model(directory, hashes(), observations())
    observations_out = []
    for name, _, part, truth in cases():
        decisions = [pick(rows[name, part, n]) for n in range(len(ORDERS))]
        agreement = decisions[0] if None not in decisions and len(set(decisions)) == 1 else None
        observations_out.append({"candidate": name, "part": part, "truth": truth,
                                 "choices": decisions, "agreement": agreement})
    metrics = {}
    for name, truth in (("omitted", 0), ("supported", 1), ("contradicted", 2)):
        review = [r for r in observations_out if r["truth"] == truth]
        metrics[name] = {"cases": len(review), "unanimous_correct": sum(r["agreement"] == truth for r in review),
                         "unanimous_wrong": sum(r["agreement"] not in (truth, None) for r in review),
                         "order_disagreement": sum(r["agreement"] is None for r in review)}
    return {"scope": "Adaptive exposed case. Each criterion is read in all three label positions. "
                     "Class-conditional accuracy and disagreement use distinct record-criterion pairs.",
            "actions_sha256": digest(directory / "actions.jsonl"),
            "metrics": metrics,
            "outcomes": observations_out}


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("mode", choices=("run", "report"))
    cli.add_argument("directory", type=Path)
    cli.add_argument("--model", type=Path)
    args = cli.parse_args()
    if args.mode == "run":
        if args.model is None:
            cli.error("run requires --model")
        run(args.model, args.directory)
    else:
        print(json.dumps(report(args.directory), indent=2))
