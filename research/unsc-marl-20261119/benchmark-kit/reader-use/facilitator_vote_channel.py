"""Extract an actor's recorded vote on an exact resolution and audit the reply."""
import argparse
from collections import Counter
import json
from pathlib import Path
from unittest.mock import patch

import facilitator_new_meetings as prior

HERE = prior.HERE
FAMILY = "facilitator-vote-channel"
CAP = 80
VOTES = {"yes": "in favour of", "no": "against", "abstain": None}
RESOLUTIONS = {"guinea": "2634 (2022)", "libya": "2796 (2025)"}
TASK = (
    "Find the vote actually recorded for the named delegation on the specified resolution. "
    "A speech about a draft, negotiation position or a different resolution is not a recorded vote. "
    "A country chairing or speaking for a group does not establish other countries' votes. "
    "If an exact passage records the requested vote, respond yes|EXACT SOURCE WORDS, "
    "no|EXACT SOURCE WORDS, or abstain|EXACT SOURCE WORDS. Copy one contiguous span, "
    "with original punctuation and no extra quotation marks. If the source does not establish "
    "the named delegation's vote on that measure, respond unknown with no explanation."
)
# Fictional cards test the channel contract. Never supply them as historical records.
CONTROLS = (
    ("scope-other-vote", "Ghana", "2634 (2022)",
     "Norway voted in favour of resolution 2634 (2022). Ghana helped prepare the draft before it went to a vote.", "unknown"),
    ("scope-other-measure", "Ghana", "2634 (2022)",
     "Ghana voted against resolution 2722 (2024) in this exercise. No votes on other measures are recorded here.", "unknown"),
    ("speech-not-vote", "China", "2634 (2022)",
     "China said the version of the piracy draft then on the table deserved support. The meeting closed before the vote.", "unknown"),
    ("group-speaker", "Ghana", "2634 (2022)",
     "Speaking for Ghana and Norway, Ghana introduced the draft. The roll call records a yes vote from Norway on resolution 2634 (2022).", "unknown"),
    ("reported-vote", "Algeria", "2796 (2025)",
     "A delegate speculated that Algeria might abstain on resolution 2796 (2025). No roll call was held in this exercise.", "unknown"),
    ("crossed-polarities", "United Kingdom", "2796 (2025)",
     "In the exercise, the United Kingdom opposed the first draft. The final roll call lists the United Kingdom among those voting yes on resolution 2796 (2025).", "yes"),
    ("recorded-no", "Ghana", "2634 (2022)",
     "For the fictional roll call on resolution 2634 (2022), Norway voted yes. Ghana appears in the list of members voting against resolution 2634 (2022).", "no"),
    ("recorded-abstention", "China", "2634 (2022)",
     "For the fictional roll call, China abstained on resolution 2634 (2022) after praising part of the draft.", "abstain"),
    ("binding-across-sentences", "United Kingdom", "2796 (2025)",
     "A vote was held on resolution 2796 (2025). Voting in favour were Algeria and the United Kingdom. No member abstained.", "yes"),
    ("range-with-exception", "Algeria", "2796 (2025)",
     "In the exercise, every member voted for resolution 2796 (2025) except Algeria, which abstained.", "abstain"),
    ("different-stage", "Algeria", "2796 (2025)",
     "Algeria voted against the oral amendment during the exercise. On resolution 2796 (2025) as a whole, Algeria voted in favour.", "yes"),
    ("ambiguous-act", "Ghana", "2634 (2022)",
     "Ghana welcomed the Council's decision to adopt resolution 2634 (2022). The vote breakdown and individual votes are omitted.", "unknown"),
)


def cards():
    for family, meeting in prior.chair.load(prior.PACK).items():
        for index, (speaker, source) in enumerate(meeting["sources"], 1):
            yield f"{family}/S{index}", speaker, RESOLUTIONS[family], source, "yes"
    for key, *row in CONTROLS:
        yield f"control/{key}", *row


def requests():
    for key, speaker, resolution, source, _ in cards():
        yield prior.transfer.prompt(key, CAP, TASK,
                                    {"delegation": speaker, "resolution": resolution, "source": source})


def episode(generate):
    wanted = list(requests())
    return [{"family": FAMILY, "final": generate(wanted[:8]) | generate(wanted[8:])}]


def pins():
    out = prior.pins()
    path = Path(__file__).resolve()
    out[str(path.relative_to(HERE.parents[1]))] = prior.runner.digest(path)
    return out


def verify(directory):
    locked = pins()
    module = prior.chair
    with patch.multiple(module, pins=lambda: locked, requests=requests, CAP=CAP, FAMILY=FAMILY):
        return module.rows(directory)


def value(row, source):
    label, delimiter, quote = row["output"].partition("|")
    label = label.strip().casefold()
    quote = quote.strip()
    if row["ended"] and label in VOTES and delimiter and quote and quote in source:
        return label, quote
    return "unknown", None


def readings(rows):
    result = {}
    for key, actor, resolution, source, expected in cards():
        label, span = value(rows[key], source)
        result[key] = {"actor": actor, "resolution": resolution, "expected": expected, "admitted": label,
                       "span": span, "output": rows[key]["output"], "input_tokens": len(rows[key]["input_ids"]),
                       "output_tokens": len(rows[key]["output_ids"])}
    return result


def report(rows):
    scores = readings(rows)
    groups = {"retrospective": Counter(), "fictional": Counter()}
    for key, row in scores.items():
        group = groups["fictional" if key.startswith("control/") else "retrospective"]
        group.update({"rows": 1, "correct": row["admitted"] == row["expected"],
                      "false_vote": row["admitted"] != "unknown" and row["admitted"] != row["expected"],
                      "missed_vote": row["admitted"] == "unknown" and row["expected"] != "unknown"})
    return {"counts": groups, "readings": scores}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("run", "score"))
    parser.add_argument("directory", type=Path)
    parser.add_argument("--model", type=Path)
    args = parser.parse_args()
    if args.mode == "run":
        with patch.multiple(prior.runner, episode=episode, locks=pins):
            prior.runner.run(args.model, args.directory)
    else:
        print(json.dumps(report(verify(args.directory)), indent=2))
