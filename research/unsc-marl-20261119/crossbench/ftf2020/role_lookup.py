"""Select an authenticated focal card by actor and action, with two label orders."""
import argparse
from itertools import batched
import json
from pathlib import Path
from unittest.mock import patch

import role_sender as old

HERE = old.HERE
partner = old.partner
CANDIDATES = {
    "us": "United States national delegation. Its explanation of the vote against the Indonesian draft.",
    "russia": "Russian Federation national delegation. Its explanation of its affirmative vote.",
    "indonesia_national": "Dian Triansyah Djani speaking for Indonesia. The proposed policy guidance in Indonesia's draft.",
    "council_president": "Dian Triansyah Djani acting as Council President. Formal transmission of the result of the written Council vote.",
    "ambiguous": "The assignment does not identify which of these actions or capacities it seeks.",
}
ORDER = (tuple(CANDIDATES), ("council_president", "indonesia_national", "ambiguous", "us", "russia"))
GUIDE = (
    "Retrieve one described archive card for the assignment. Match the institutional action and capacity as well as the person. "
    "A national statement about a draft and the Council President's transmission of a certified vote result are different acts "
    "even when signed by the same person. If the assignment does not distinguish any card, choose the ambiguous option. "
    "Return one letter from the options. Do not add other text."
)
FRESH = {
    "fresh/national_no_title": ("What did Djani say the draft sponsored by his country would help governments do?", "indonesia_national"),
    "fresh/procedure_no_title": ("Which record shows Djani forwarding the Council's tally to the members after the written voting closed?", "council_president"),
    "fresh/national_with_president": ("The Council President also spoke for Indonesia. Find only what he argued on behalf of his country about the draft's guidance.", "indonesia_national"),
    "fresh/procedure_with_country": ("Indonesia held the presidency when the written vote closed. Find the act that formally notified the members of the result.", "council_president"),
    "fresh/ambiguous_person": ("Locate the material associated with Dian Triansyah Djani on this docket.", "ambiguous"),
    "fresh/ambiguous_vote": ("Retrieve the Council material about the vote.", "ambiguous"),
}


def examples():
    return {
        **{f"{phase}/{key}": (old.ASSIGNMENTS[key][i], key)
           for i, phase in enumerate(("probe", "mission")) for key in old.corroboration.KEYS},
        **FRESH,
    }


def requests():
    for name, (assignment, _) in examples().items():
        for index, order in enumerate(ORDER):
            offered = dict(zip("ABCDE", (CANDIDATES[key] for key in order), strict=True))
            yield partner.replay.request(f"{name}/{index}", 4, GUIDE,
                                         {"assignment": assignment, "archive_cards": offered}, [])


def episode(generate):
    rows = {}
    for group in batched(requests(), 6):
        rows.update(generate(list(group)))
    return [{"family": old.corroboration.load()["id"], "final": rows}]


def locks():
    paths = (Path(__file__), HERE / "joint-repair-results.json", HERE / "role-evidence/actions.json")
    return {**old.locks(), "role_lookup": partner.digest(paths[0]),
            **{str(path.relative_to(HERE)): partner.digest(path) for path in paths[1:]}}


def run(directory):
    with patch.object(partner.runner, "episode", episode), patch.object(partner.runner, "locks", locks):
        partner.runner.run(Path(partner.read(partner.writer.MODEL)["model"]), directory)


def decode(row, order):
    if row["ended"] and row["output"] in tuple("ABCDE"):
        return order[ord(row["output"]) - ord("A")]
    return None


def report(directory):
    with patch.object(partner.replay, "episode", episode), patch.object(partner.replay, "locks", locks):
        rows = partner.replay.verify(directory)
    repairs = partner.read(HERE / "joint-repair-results.json")["final_sender"]
    results = {}
    for name, (_, expected) in examples().items():
        labels = [decode(rows[f"{name}/{i}"], order) for i, order in enumerate(ORDER)]
        agreed = labels[0] if labels[0] == labels[1] else None
        source = agreed if agreed and agreed != "ambiguous" else None
        bit = repairs[old.corroboration.KEYS.index(source)] if source else None
        results[name] = {"reference": expected, "labels": labels, "confirmed_source": source,
                         "request_bit": bit, "exact": agreed == expected}
    return {"scope": "Fresh label-swapped retrieval. A disagreement or ambiguous answer supplies no authenticated "
                     "focal source to the existing repaired policy. No training labels or peer observations enter the prompt.",
            "trace_sha256": partner.digest(directory / "transcript.jsonl"), "records": results}


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("mode", choices=("run", "score"))
    cli.add_argument("directory", type=Path)
    args = cli.parse_args()
    if args.mode == "run":
        run(args.directory)
    else:
        print(json.dumps(report(args.directory), ensure_ascii=False, indent=2))
