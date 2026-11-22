"""Resolve card identity and intent with stable semantic record identifiers."""
import argparse
from itertools import batched
import json
from pathlib import Path
from unittest.mock import patch

import intent_set as first

HERE = first.HERE
partner = first.partner
IDS = {"us": "US", "russia": "RUSSIA", "indonesia_national": "INDONESIA", "council_president": "RESULT"}
ALIASES = {alias: key for key, alias in IDS.items()}
GUIDE = (
    "Return the archive intent using the listed record IDs. Use ONE ID for a specified record, ALL ID ID "
    "for records that are all requested, ANY ID ID for explicitly acceptable alternatives, or UNSPECIFIED. "
    "Examples: ONE RESULT, ALL US RUSSIA, ANY INDONESIA RESULT, UNSPECIFIED. "
    "An official transmission is a document or act that gives members the Council's written result, not a "
    "person's remarks about a result. Mentioning an actor, draft or vote without identifying the requested act "
    "or material does not select a card. Records said to be excluded, already held or merely related are not "
    "requested. Return only the intent and IDs."
)
RESERVE = {
    "new/official_record": ("Pull the written notification conveying the certified result to Council members. No national explanation is needed.", "one", ("council_president",)),
    "new/two_voices": ("Retrieve the Indonesian sponsor's policy case together with the Russian delegation's vote explanation.", "all", ("indonesia_national", "russia")),
    "new/either_but_not_both": ("Give me either the Russian explanation of its vote or Indonesia's assessment of the draft. One of those is enough.", "any", ("russia", "indonesia_national")),
    "new/same_person_no_role": ("Show me the documents concerning Djani's involvement in the balloting on that draft.", "unspecified", ()),
}


def examples():
    return {**first.examples(), **RESERVE}


def requests():
    for name, (text, _, _) in examples().items():
        for i, order in enumerate(first.ORDERS):
            offered = {IDS[key]: first.CARDS[key] for key in order}
            yield partner.replay.request(f"{name}/{i}", 18, GUIDE, {"assignment": text, "archive_cards": offered}, [])


def episode(generate):
    result = {}
    for group in batched(requests(), 8):
        result.update(generate(list(group)))
    return [{"family": first.baseline.initial.old.corroboration.load()["id"], "final": result}]


def locks():
    return {**first.locks(), "semantic_intent": partner.digest(Path(__file__)),
            "first_results": partner.digest(HERE / "intent-evidence/results.json")}


def run(directory):
    with patch.object(partner.runner, "episode", episode), patch.object(partner.runner, "locks", locks):
        partner.runner.run(Path(partner.read(partner.writer.MODEL)["model"]), directory)


def parse(row):
    if not row["ended"]:
        return None
    content = row["output"].split()
    if content == ["UNSPECIFIED"]:
        return "unspecified", ()
    if len(content) < 2 or content[0] not in ("ONE", "ALL", "ANY"):
        return None
    kind, *ids = content
    if not set(ids) <= ALIASES.keys() or len(ids) != len(set(ids)):
        return None
    if (kind == "ONE") != (len(ids) == 1):
        return None
    return kind.lower(), tuple(sorted(ALIASES[key] for key in ids))


def result(directory):
    with patch.object(partner.replay, "episode", episode), patch.object(partner.replay, "locks", locks):
        rows = partner.replay.verify(directory)
    old = partner.read(HERE / "intent-evidence/results.json")["records"]
    answers = {}
    for name, (text, kind, keys) in examples().items():
        labels = [parse(rows[f"{name}/{i}"]) for i in range(2)]
        consensus = labels[0] if labels[0] == labels[1] else None
        truth = kind, tuple(sorted(keys))
        answers[name] = {"assignment": text, "reference": truth, "parsed_by_order": labels,
                         "consensus": consensus, "exact": truth == consensus,
                         "previous_exact": old[name]["exact"] if name in old else None}
    return {"scope": "Stable semantic identifiers and explicit request operators. Card presentation order is still "
                     "changed. The 20 previously measured prompts are development cases. The four additional prompts "
                     "were fixed before collecting this trace.",
            "trace_sha256": partner.digest(directory / "transcript.jsonl"), "records": answers}


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("mode", choices=("run", "score"))
    cli.add_argument("directory", type=Path)
    args = cli.parse_args()
    if args.mode == "run":
        run(args.directory)
    else:
        print(json.dumps(result(args.directory), ensure_ascii=False, indent=2))
