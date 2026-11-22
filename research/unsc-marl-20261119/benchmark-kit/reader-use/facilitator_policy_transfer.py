"""Transfer frozen facilitator policies and local readings to two other UN records."""
import argparse
from collections import defaultdict
from hashlib import sha256
import json
from pathlib import Path
from unittest.mock import patch

import facilitator_policy as base
from facilitator_policy_audit import freeze

HERE = base.HERE
protocol = base.endpoint
runner = protocol.runner
CROSS = protocol.common_ground.CROSS
FROZEN = HERE / "facilitator-policy-balanced.json"
OLD = HERE / "facilitator-policy.json"
UNIFIL = CROSS / "unifil-record.json"
COLOMBIA = CROSS / "colombia2023/case.json"

# Propositions are about documented positions. The second dossier is
# independent of the previous facilitator replay and remains excluded from fit.
PANELS = {
    "unifil": (
        ("Brazil and China supported UNIFIL's continued work.", ("supported UNIFIL's continued work",)*2,
         ("supports", "supports")),
        ("Brazil and China each said the text fully addressed Lebanon's concerns.", ("said the text fully addressed Lebanon's concerns",)*2,
         ("unknown", "contradicts")),
        ("Brazil and China both stressed host-State sovereignty and consent.", ("stressed host-State sovereignty and consent",)*2,
         ("unknown", "supports")),
        ("Brazil and China each said the text addressed some of Lebanon's concerns.", ("said the text addressed some of Lebanon's concerns",)*2,
         ("supports", "unknown")),
    ),
    "colombia": (
        ("Brazil and the African members saw a possible future role for EMC ceasefire verification, subject to conditions.",
         ("expressed support or hope for possible future EMC ceasefire verification subject to conditions",)*2,
         ("supports", "supports")),
        ("Brazil and the African members called for immediate EMC ceasefire verification without further conditions.",
         ("called for immediate EMC ceasefire verification without further conditions",)*2, ("contradicts", "contradicts")),
        ("Brazil and the African members pledged to encourage progress on the Ethnic Chapter.",
         ("pledged to encourage progress on the Ethnic Chapter",)*2, ("unknown", "supports")),
        ("Both speakers said the Security Council should respond to the priorities expressed by Colombia's Government.",
         ("said the Security Council should respond to Colombia's Government's stated priorities",)*2,
         ("supports", "unknown")),
    ),
}


def packets():
    unifil = {row["id"]: row["text"] for row in protocol.delivery.load(UNIFIL)["evidence"]}
    colombia = {k: v for role in protocol.delivery.load(COLOMBIA)["roles"].values() for k,v in role.items()}
    return {"unifil": (("Brazil",unifil["brazil"]), ("China",unifil["china"])),
            "colombia": (("Brazil",colombia["BRAZIL"]), ("The three African members",colombia["A3"]))}


def prompts():
    task = ("Check whether this one official passage establishes the stated position for the specific speaker, "
            "contradicts it, or leaves it unknown. Do not attribute a claim by a representative to another body "
            "or convert support for a measure into a recorded vote.")
    for family, docs in packets().items():
        for number, (_, acts, _) in enumerate(PANELS[family]):
            for pos, ((speaker, card), act) in enumerate(zip(docs, acts, strict=True)):
                yield from protocol.encoded((family, number, pos), task,
                                            {"one_side_of_claim": f"{speaker} {act}.",
                                             "source": speaker, "documentary_passage": card}, protocol.RELATIONS)


def locks():
    paths = (Path(__file__), Path(base.__file__), Path(protocol.__file__), Path(runner.__file__),
             UNIFIL, COLOMBIA, FROZEN, OLD)
    return {str(p.resolve().relative_to(HERE.parents[1])): sha256(p.read_bytes()).hexdigest() for p in paths}


def policy(path):
    return {freeze(r["state"]): r["probabilities"] for r in protocol.delivery.load(path)["policy"]}


def score(directory):
    with patch.multiple(runner, observations=prompts, hashes=locks):
        raw = runner.read(directory)
    learned, earlier = policy(FROZEN), policy(OLD)
    data = []
    for family, cases in PANELS.items():
        for i, (proposal, _, truth) in enumerate(cases):
            votes = [protocol.votes(raw, (family, i, pos), protocol.RELATIONS) for pos in range(2)]
            observed = tuple(protocol.stable(result) or "unknown" for result in votes)
            gold = base.decision(truth, base.TARGETS)
            comparison = {}
            for inventory in ("overlap", "split"):
                reader = base.base.roster(inventory)
                variants = {name: (name, learned) for name in ("learned", "learned_erased", "greedy", "greedy_erased")}
                variants["uniform_fit"] = "learned", earlier
                comparison[inventory] = {}
                for name, (kind, weights) in variants.items():
                    figures, masks = base.distribution(kind, weights, reader, truth, observed)
                    # A true revision is useful only when the evidence that
                    # actually arrived justifies the revision.
                    certified = defaultdict(float)
                    for seen, mass in masks.items():
                        available = base.decision(truth, seen)
                        proposed = base.decision(observed, seen)
                        certified["true_retain"] += mass * (available == proposed == "retain")
                        certified["true_revise"] += mass * (available == proposed == "revise")
                        certified["false_action"] += mass * (proposed != "withhold" and available != proposed)
                    weighted_cost = figures["cost"]
                    net = certified["true_retain"] + certified["true_revise"] - certified["false_action"] - weighted_cost
                    comparison[inventory][name] = dict(certified) | {"cost": weighted_cost, "net": net}
            data.append({"family": family, "proposal": proposal, "true_relations": truth, "model_votes": votes,
                         "observed_relations": observed, "required_full_action": gold,
                         "full_observed_action": base.decision(observed, base.TARGETS), "replay": comparison})
    means = {}
    for inventory, variants in data[0]["replay"].items():
        means[inventory] = {name: {key: sum(row["replay"][inventory][name][key] for row in data)/len(data)
                                   for key in metrics} for name, metrics in variants.items()}
    exact = sum(t == o for row in data for t, o in zip(row["true_relations"],row["observed_relations"],strict=True))
    false_retain = sum(row["full_observed_action"] == "retain" and row["required_full_action"] != "retain"
                       for row in data)
    return {"scope": "Frozen routing policies with new documentary claim panels. "
                     "Subclaims and source maps are authored and the dockets are previously exposed elsewhere. "
                     "The endpoint certifies the disposition against actually received evidence. No replacement generation.",
            "source_relation_exact": exact, "full_packet_false_retain": false_retain, "panels": data, "replay": means}


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("mode", choices=("run", "score"))
    cli.add_argument("directory", type=Path)
    cli.add_argument("--model", type=Path)
    args = cli.parse_args()
    if args.mode == "run":
        with patch.multiple(runner, observations=prompts, hashes=locks):
            runner.score(args.model, args.directory)
    else:
        print(json.dumps(score(args.directory), indent=2))
