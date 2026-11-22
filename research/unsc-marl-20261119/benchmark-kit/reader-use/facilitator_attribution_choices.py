"""Separate attribution matching from the final record body."""
import argparse
from collections import defaultdict
import json
from pathlib import Path
from unittest.mock import patch

import facilitator_event_transfer as transfer
import facilitator_verified_brief as old

HERE = old.HERE
PACK = HERE / "facilitator_attribution_choices.json"
FAMILY = "facilitator-attribution-choices"
CAP = 95
BODY_CAP = 105
runner = old.runner
ORDERS = ((0, 1, 2), (1, 2, 0), (2, 0, 1))
ARMS = ("body_alone", "with_findings")
RELATIONS = ("supports", "contradicts", "unknown")
CHECK = (
    "Which of the candidate reports is established by the documentary card? Compare each candidate's exact "
    "actor, requested act, object and qualification to what that person actually said or did. Choose the "
    "insufficient evidence candidate if neither factual alternative is established. A vote for an instrument does "
    "not settle preference between instruments. Attribute just the position the source establishes. "
    "Copy the complete selected candidate exactly, with no quotation marks or explanation."
)
BODY = (
    "Supply just the two delegation sentences for a documentary record, one sentence per delegation. "
    "Cite each sentence with its exact source ID [S1] or [S2]. Answer the precise target in the original "
    "assertion. For a side whose status is unestablished, state that the card leaves that specific "
    "question open, and you may add the person's relevant actual position from the card. Preserve qualifications. "
    "When findings are supplied, use them as working advice and check them against the source. "
    "Keep the two sentences on one line in at most 40 words. Omit the Council outcome and any heading."
)


def panels():
    verified = {name: (docket, item) for name, docket, item, _ in old.panels()}
    transfers = {name: (predicate, truth, [{"actor": actor, "card": source} for actor, source in sources])
                 for name, _, predicate, truth, sources in transfer.panels()}
    for name, config in transfer.chair.load(PACK).items():
        if config["parent"] == "verified":
            docket, item = verified[name]
            config |= {"council": docket["council"], "sources": docket["sources"],
                       "predicate": item["predicate"], "expected": item["expected"]}
        elif config["parent"] == "transfer":
            predicate, truth, sources = transfers[name]
            config |= {"predicate": predicate, "expected": truth, "sources": sources}
        yield name, config


def alternatives(config, actor):
    return (f"{actor} {config['predicate']}.", f"{actor} {config['opposite']}.",
            "The supplied card does not establish either position.")


def requests():
    for name, panel in panels():
        for i, source in enumerate(panel["sources"], 1):
            candidates = alternatives(panel, source["actor"])
            for version, order in enumerate(ORDERS, 1):
                payload = {"documentary_card": source["card"], "speaker": source["actor"],
                           "candidate_reports": [candidates[i] for i in order]}
                yield transfer.prompt(f"{name}/S{i}/read{version}", CAP, CHECK, payload)


def readings(rows):
    results = {}
    for name, panel in panels():
        for i, source in enumerate(panel["sources"], 1):
            candidates = alternatives(panel, source["actor"])
            observed = []
            for version in range(1, 4):
                row = rows[f"{name}/S{i}/read{version}"]
                output = row["output"]
                relation = RELATIONS[candidates.index(output)] if row["ended"] and output in candidates else None
                observed.append(relation)
            stable = observed[0] if observed[0] is not None and all(r == observed[0] for r in observed) else None
            results[f"{name}/S{i}"] = {"observations": observed, "stable": stable,
                                       "fallback": stable or "unknown"}
    return results


def bodies(rows):
    signals = readings(rows)
    for name, panel in panels():
        payload = {"assertions": {}, "cards": {}}
        for i, source in enumerate(panel["sources"], 1):
            sid = f"S{i}"
            payload["assertions"][sid] = alternatives(panel, source["actor"])[0]
            payload["cards"][sid] = source["card"]
        for arm in ARMS:
            fields = dict(payload)
            if arm == "with_findings":
                fields["findings"] = {sid: signals[f"{name}/{sid}"]["fallback"] for sid in payload["cards"]}
            yield transfer.prompt(f"{name}/{arm}/body", BODY_CAP, BODY, fields)


def episode(generate):
    wanted = list(requests())
    rows = {}
    for start in range(0, len(wanted), 8):
        rows.update(generate(wanted[start:start + 8]))
    rows.update(generate(list(bodies(rows))))
    return [{"family": FAMILY, "final": rows}]


def pins():
    locks = old.pins()
    for file in (PACK, Path(__file__)):
        locks[str(file.resolve().relative_to(HERE.parents[1]))] = runner.digest(file)
    return locks


def verify(directory):
    locks = pins()
    with patch.multiple(transfer, local=requests, audits=lambda _: (), syntheses=bodies,
                        pins=lambda: locks, FAMILY=FAMILY):
        return transfer.read(directory)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("run", "verify"))
    parser.add_argument("directory", type=Path)
    parser.add_argument("--model", type=Path)
    args = parser.parse_args()
    if args.mode == "run":
        with patch.multiple(runner, episode=episode, locks=pins):
            runner.run(args.model, args.directory)
    else:
        print(json.dumps({"verified_generations": len(verify(args.directory))}))
