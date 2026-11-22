"""Check whether the assignment scopes a single archive object before lookup."""
import argparse
from itertools import batched
import json
from pathlib import Path
from unittest.mock import patch

import role_lookup as lookup

HERE = lookup.HERE
partner = lookup.partner
GUIDE = (
    "Judge how specific an archival retrieval request is. YES means the request itself specifies a distinguishing "
    "act or capacity for a single record. Wanting a country's reasons for its vote, its view of a proposal, or the "
    "officer's act of notifying Council members are specific. NO means the request asks only about the person, docket, "
    "or voting in general, without identifying a statement, reason, position, formal document or act. Do not assume "
    "an unspecified person acts in only one capacity. Output exactly YES or NO."
)
CONTROLS = {
    "gate/abstract_person": ("Tell me where to find things connected to the Indonesian representative in this file.", False),
    "gate/abstract_procedure": ("Get the material concerning the Council's business on the Indonesian text.", False),
    "gate/specific_position": ("Find Indonesia's case for what its proposal would do for Member States.", True),
    "gate/specific_notice": ("Retrieve the act by which members were formally informed of the completed written ballot.", True),
}


def examples():
    return {**{key: (text, expected != "ambiguous") for key, (text, expected) in lookup.examples().items()}, **CONTROLS}


def requests():
    for key, (text, _) in examples().items():
        yield partner.replay.request(key, 4, GUIDE, {"assignment": text}, [])


def episode(generate):
    rows = {}
    for group in batched(requests(), 6):
        rows.update(generate(list(group)))
    return [{"family": lookup.old.corroboration.load()["id"], "final": rows}]


def locks():
    return {**lookup.locks(), "scope_gate": partner.digest(Path(__file__)),
            "lookup_trace": partner.digest(HERE / "lookup-evidence/transcript.jsonl"),
            "lookup_decisions": partner.digest(HERE / "lookup-evidence/results.json")}


def run(directory):
    with patch.object(partner.runner, "episode", episode), patch.object(partner.runner, "locks", locks):
        partner.runner.run(Path(partner.read(partner.writer.MODEL)["model"]), directory)


def report(directory):
    with patch.object(partner.replay, "episode", episode), patch.object(partner.replay, "locks", locks):
        outputs = partner.replay.verify(directory)
    lookup_results = partner.read(HERE / "lookup-evidence/results.json")["records"]
    results = {}
    for key, (_, truth) in examples().items():
        row = outputs[key]
        verdict = {"YES": True, "NO": False}.get(row["output"]) if row["ended"] else None
        entry = {"reference_scoped": truth, "scoped": verdict, "correct": verdict == truth}
        if key in lookup_results:
            record = lookup_results[key]
            chosen = record["confirmed_source"] if verdict is True else None
            entry.update(reference_source=record["reference"], confirmed_source=chosen,
                         request_bit=record["request_bit"] if chosen else None,
                         correct_or_abstained=(chosen == record["reference"] if truth else chosen is None))
        results[key] = entry
    return {"scope": "The YES/NO scope check sees only the assignment, with no card candidates or protocol bit. "
                     "It can withhold an otherwise stable lookup. Authored probes in one written-vote docket.",
            "trace_sha256": partner.digest(directory / "transcript.jsonl"), "results": results}


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("mode", choices=("run", "score"))
    cli.add_argument("directory", type=Path)
    args = cli.parse_args()
    if args.mode == "run":
        run(args.directory)
    else:
        print(json.dumps(report(args.directory), ensure_ascii=False, indent=2))
