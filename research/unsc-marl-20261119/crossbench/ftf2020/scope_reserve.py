"""Challenge the frozen scope gate with new one-card and multi-card requests."""
import argparse
from itertools import batched
import json
from pathlib import Path
from unittest.mock import patch

import scope_gate as trained

partner = trained.partner
HERE = trained.HERE
CASES = {
    "notification_excludes_national": ("Find the result letter rather than what Djani argued for his government when supporting the proposal.", True),
    "national_excludes_notification": ("Retrieve the case Indonesia made as sponsor. Leave out the tally its representative forwarded.", True),
    "notification_with_actor": ("The member who chaired the Council happened to be Djani. Which communication gave delegates the certified voting outcome?", True),
    "foreign_vote_explanation": ("What grounds did Russia give for voting yes despite its concern about return to countries of origin?", True),
    "both_roles": ("Find what Djani argued as Indonesia's representative and the message he later sent as Council President.", False),
    "either_role": ("Find either the Indonesian policy explanation or the notice transmitting the result. Either one would be fine.", False),
    "both_delegations": ("Retrieve both the explanation of the Russian yes vote and the explanation of the United States' no vote.", False),
    "thin_statement_identity": ("What did Djani say about the result of the vote?", False),
    "docket_only": ("Find the Indonesian file about the voting on the proposal.", False),
    "national_only": ("Find the American delegate's explanation of why her country opposed the draft.", True),
}


def requests():
    for name, (assignment, _) in CASES.items():
        yield partner.replay.request(name, 4, trained.GUIDE, {"assignment": assignment}, [])


def episode(generate):
    rows = {}
    for batch in batched(requests(), 5):
        rows.update(generate(list(batch)))
    return [{"family": trained.lookup.old.corroboration.load()["id"], "final": rows}]


def locks():
    return {**trained.locks(), "scope_reserve": partner.digest(Path(__file__)),
            "calibration_trace": partner.digest(HERE / "scope-evidence/transcript.jsonl"),
            "scoped_lookup_results": partner.digest(HERE / "scoped-lookup-evidence/results.json")}


def run(directory):
    with patch.object(partner.runner, "episode", episode), patch.object(partner.runner, "locks", locks):
        partner.runner.run(Path(partner.read(partner.writer.MODEL)["model"]), directory)


def report(directory):
    with patch.object(partner.replay, "episode", episode), patch.object(partner.replay, "locks", locks):
        rows = partner.replay.verify(directory)
    records = {}
    for key, (wording, expected) in CASES.items():
        row = rows[key]
        verdict = {"YES": True, "NO": False}.get(row["output"]) if row["ended"] else None
        records[key] = {"text": wording, "reference_single_record": expected,
                        "observed_single_record": verdict, "correct": verdict == expected}
    return {"scope": "The previously frozen scope prompt on ten fresh same-docket controls. "
                     "Requests for multiple records and unspecified alternatives are unsuitable for the current one-card runtime.",
            "trace_sha256": partner.digest(directory / "transcript.jsonl"), "records": records}


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("mode", choices=("run", "score"))
    cli.add_argument("directory", type=Path)
    args = cli.parse_args()
    if args.mode == "run":
        run(args.directory)
    else:
        print(json.dumps(report(args.directory), indent=2, ensure_ascii=False))
