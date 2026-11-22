"""Test exact vote extraction with competing records and document-isolation control."""
import argparse
from itertools import product
import json
from pathlib import Path
from unittest.mock import patch

import facilitator_vote_channel_format as frozen

HERE = frozen.prior.HERE
PACK = HERE / "facilitator-mixed-votes.json"
FAMILY = "facilitator-mixed-votes"
CAP = 160
runner = frozen.prior.runner
ARMS = ("combined", "isolated")
POLARITIES = {"yes": "In favour", "no": "Against", "abstain": "Abstaining"}
TASK = (
    "Find the recorded vote of the named delegation on the exact requested document. "
    "Match the document symbol before using any vote group. An amendment and its parent draft have separate votes. "
    "On a single line write the vote label (yes, no, or abstain), a comma, and the exact full vote-group line "
    "from the source. Include its document symbol, heading, and list, preserving spelling and punctuation. "
    "Write just unknown if no vote establishes the requested delegation's position."
)


def meetings():
    return frozen.prior.chair.load(PACK)


def records():
    for family, meeting in meetings().items():
        blocks = {}
        for row in meeting["records"]:
            assert sum(len(row[p]) for p in POLARITIES) == len(set(sum((row[p] for p in POLARITIES), []))) == 15
            document = row["id"]
            header = f"{meeting['meeting']} recorded the vote on {row['kind']} {document}"
            if row.get("parent"):
                header += f" to draft resolution {row['parent']}"
            lines = {label: f"{document} {heading}: {', '.join(row[label])}."
                     for label, heading in POLARITIES.items()}
            blocks[document] = (row, lines, "\n".join([f"{header}.", *lines.values(), row["outcome"]]))
        for (document, (record, lines, block)), actor, arm in product(blocks.items(), meeting["actors"], ARMS):
            evidence = "\n\n".join(item[2] for item in blocks.values()) if arm == "combined" else block
            label, = [p for p in POLARITIES if actor in record[p]]
            key = f"{family}/{document.replace('/', '-')}/{actor.replace(' ', '-')}/{arm}"
            yield key, actor, document, evidence, label, lines[label]


def requests():
    for key, actor, document, evidence, _, _ in records():
        yield frozen.prior.transfer.prompt(key, CAP, TASK, {"delegation": actor, "document": document, "source": evidence})


def episode(generate):
    wanted = list(requests())
    results = {}
    for start in range(0, len(wanted), 8):
        results.update(generate(wanted[start:start + 8]))
    return [{"family": FAMILY, "final": results}]


def pins():
    checks = frozen.pins()
    for path in (PACK, Path(__file__)):
        checks[str(path.resolve().relative_to(HERE.parents[1]))] = runner.digest(path)
    return checks


def verify(directory):
    locked = pins()
    module = frozen.prior.chair
    with patch.multiple(module, pins=lambda: locked, requests=requests, CAP=CAP, FAMILY=FAMILY):
        return module.rows(directory)


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
        print(json.dumps({"generations": len(verify(args.directory))}))
