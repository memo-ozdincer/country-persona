"""Carry the frozen witness verifier into a broader Council record task."""
import argparse
import json
from pathlib import Path
from unittest.mock import patch

import facilitator_event_transfer as common
import facilitator_witness_contrast as previous
from facilitator_witness_contrast_score import answer
import facilitator_vote_witness_rule as vote

HERE = common.HERE
PACK = HERE / "facilitator_verified_brief-packet.json"
FAMILY = "facilitator-verified-brief"
runner = common.runner
FAMILIES = ("pooled", "direct", "hybrid")
FINAL_CAP = 150
TASK = (
    "Write a short documentary facilitator record. Begin with retain, revise, or withhold, then a vertical bar. "
    "Retain if both claims are established, revise if either is contradicted, and otherwise withhold. "
    "In at most 75 words give the Council's recorded disposition and vote count [S0], the relevant position "
    "or exact evidence gap for each speaker, and the source citation [S1] or [S2] after each factual attribution. "
    "Preserve differences between an adopted text, a vote on an amendment, a policy preference, and subsequent "
    "implementation. A verifier's open result means its witness did not rule the assertion out, not that it "
    "proved the assertion. A compatible witness may leave a claim open. Verify documentary facts against the sources."
)


def panels():
    for label, docket in common.chair.load(PACK).items():
        sources = {"S0": docket["council"]} | {f"S{i+1}": card["card"] for i, card in enumerate(docket["sources"])}
        for item in docket["panels"]:
            yield f"{label}/{item['id']}", docket, item, sources


def requests():
    for panel, docket, item, _ in panels():
        for i, (speaker, excerpt) in enumerate(zip(docket["sources"], item["witnesses"], strict=True), 1):
            payload = {"assertion": f"{speaker['actor']} {item['predicate']}.", "cited_words": excerpt,
                       "official_card": speaker["card"]}
            assert payload["official_card"].count(excerpt) == 1
            for arm, prompt in zip(previous.ARMS, (previous.DIRECT, previous.COMPARE), strict=True):
                yield common.prompt(f"{panel}/S{i}/{arm}", previous.CAP, prompt, payload)


def checks(rows):
    values = {}
    for request in requests():
        key = request["id"]
        arm = key.rsplit("/", 1)[1]
        payload = json.loads(request["messages"][1]["content"])
        proposed, valid, _ = answer(rows[key], arm, strip_separator=(arm == "compare_first"))
        verdict = proposed if valid else "unclassified"
        hard = vote.check(payload["assertion"], payload["cited_words"], payload["official_card"]) if arm == "compare_first" else None
        values[key] = {"verdict": hard or verdict, "proposed": proposed, "valid": valid,
                       "bound_vote_rule": hard is not None}
    return values


def finals(rows):
    readings = checks(rows)
    for panel, docket, item, sources in panels():
        assertions = {f"S{i+1}": f"{source['actor']} {item['predicate']}." for i, source in enumerate(docket["sources"])}
        payload = {"assertions": assertions, "sources": sources,
                   "candidate_excerpts": {f"S{i+1}": excerpt for i, excerpt in enumerate(item["witnesses"])}}
        for arm in FAMILIES:
            fields = dict(payload)
            if arm != "pooled":
                gate = "direct" if arm == "direct" else "compare_first"
                fields["witness_checks"] = {sid: readings[f"{panel}/{sid}/{gate}"]["verdict"] for sid in assertions}
            yield common.prompt(f"{panel}/{arm}/final", FINAL_CAP, TASK, fields)


def episode(generate):
    wanted = list(requests())
    rows = generate(wanted[:8]) | generate(wanted[8:])
    rows.update(generate(list(finals(rows))))
    return [{"family": FAMILY, "final": rows}]


def pins():
    locks = previous.pins()
    from facilitator_witness_contrast_score import __file__ as scorer
    for file in (Path(__file__), PACK, Path(vote.__file__), Path(scorer)):
        locks[str(file.resolve().relative_to(HERE.parents[1]))] = runner.digest(file)
    return locks


def verify(directory):
    locked = pins()
    with patch.multiple(common, local=requests, audits=lambda _: (), syntheses=finals,
                        pins=lambda: locked, FAMILY=FAMILY):
        return common.read(directory)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode", choices=("run", "verify"))
    p.add_argument("directory", type=Path)
    p.add_argument("--model", type=Path)
    args = p.parse_args()
    if args.mode == "run":
        with patch.multiple(runner, episode=episode, locks=pins):
            runner.run(args.model, args.directory)
    else:
        print(json.dumps({"verified_generations": len(verify(args.directory))}))
