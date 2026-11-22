"""Resolve requests as one card, conjunction, alternative or unspecified."""
import argparse
from itertools import batched
import json
from pathlib import Path
import re
from unittest.mock import patch

import scope_reserve as reserve
import scoped_lookup as baseline

HERE = baseline.HERE
partner = baseline.partner
CARDS = {key: value for key, value in baseline.initial.CANDIDATES.items() if key != "ambiguous"}
ORDERS = baseline.ORDERS
GUIDE = (
    "Resolve the request against the archive cards. Return one letter for exactly one requested record, letters "
    "joined with + when every listed record is requested, or letters joined with / when any one of those "
    "records would satisfy the request. Use ? when the request leaves which record it wants unspecified. "
    "Count records requested, ignoring records merely mentioned, excluded or given as background. "
    "National policy remarks and formally reporting a Council ballot are different records even for the same person. "
    "Examples of answer format: A, A+C, A/C, ?. Output only the answer."
)
NAT = "indonesia_national"
CHAIR = "council_president"
OLD = {
    "notification_excludes_national": ("one", (CHAIR,)),
    "national_excludes_notification": ("one", (NAT,)),
    "notification_with_actor": ("one", (CHAIR,)),
    "foreign_vote_explanation": ("one", ("russia",)),
    "both_roles": ("all", (NAT, CHAIR)),
    "either_role": ("any", (NAT, CHAIR)),
    "both_delegations": ("all", ("russia", "us")),
    "thin_statement_identity": ("unspecified", ()),
    "docket_only": ("unspecified", ()),
    "national_only": ("one", ("us",)),
}
NEW = {
    "exclude_turnaround": ("I already have the letter conveying the Council's tally. Find Djani's remarks on behalf of Indonesia about what its draft would achieve.", "one", (NAT,)),
    "result_only": ("Please leave the sponsor's policy explanation aside. What record formally communicated the completed written ballot?", "one", (CHAIR,)),
    "not_a_second_retrieval": ("Russia raised repatriation like the United States did. Retrieve the latter's explanation of its negative vote alone.", "one", ("us",)),
    "separate_artifacts": ("I need the Indonesian sponsor's explanation and, as a separate item, the letter reporting the completed ballot.", "all", (NAT, CHAIR)),
    "compare_dissent": ("Collect the two national explanations for the American no and Russian yes votes so I can compare them.", "all", ("us", "russia")),
    "mixed_pair": ("Please locate Russia's explanation of its affirmative vote and the Council President's official notification.", "all", ("russia", CHAIR)),
    "either_delegation": ("Get one national explanation, either from Russia or from the United States. I do not need both.", "any", ("us", "russia")),
    "either_capacity": ("One item is enough. Pick either what Djani said for Indonesia as sponsor or his formal transmission as Council President.", "any", (NAT, CHAIR)),
    "person_without_act": ("Please pull up Djani's part of the record on the written ballot.", "unspecified", ()),
    "docket_without_act": ("Can you find the relevant material on the Indonesian draft?", "unspecified", ()),
}


def examples():
    assert OLD.keys() == reserve.CASES.keys()
    return {**{f"reserve/{k}": (reserve.CASES[k][0], kind, keys) for k, (kind, keys) in OLD.items()},
            **{f"fresh/{k}": v for k, v in NEW.items()}}


def requests():
    for name, (text, _, _) in examples().items():
        for i, order in enumerate(ORDERS):
            offered = dict(zip("ABCD", (CARDS[key] for key in order), strict=True))
            yield partner.replay.request(f"{name}/{i}", 10, GUIDE, {"assignment": text, "archive_cards": offered}, [])


def episode(generate):
    rows = {}
    for group in batched(requests(), 8):
        rows.update(generate(list(group)))
    return [{"family": baseline.initial.old.corroboration.load()["id"], "final": rows}]


def locks():
    return {**baseline.locks(), "intent_set": partner.digest(Path(__file__)),
            "reserve": partner.digest(HERE / "scope-reserve-evidence/results.json")}


def run(directory):
    with patch.object(partner.runner, "episode", episode), patch.object(partner.runner, "locks", locks):
        partner.runner.run(Path(partner.read(partner.writer.MODEL)["model"]), directory)


def decode(row, order):
    if not row["ended"]:
        return None
    output = re.sub(r"\s+", "", row["output"])
    if output == "?":
        return "unspecified", ()
    if not re.fullmatch(r"[A-D](?:\+[A-D])*|[A-D](?:/[A-D])+", output):
        return None
    entries = re.split(r"[+/]", output)
    if len(entries) != len(set(entries)):
        return None
    kind = "one" if len(entries) == 1 else "all" if "+" in output else "any"
    return kind, tuple(sorted(order[ord(letter) - ord("A")] for letter in entries))


def report(directory):
    with patch.object(partner.replay, "episode", episode), patch.object(partner.replay, "locks", locks):
        rows = partner.replay.verify(directory)
    results = {}
    for name, (text, kind, keys) in examples().items():
        modes = [decode(rows[f"{name}/{i}"], order) for i, order in enumerate(ORDERS)]
        agreed = modes[0] if modes[0] == modes[1] else None
        truth = kind, tuple(sorted(keys))
        chosen = agreed[1][0] if agreed is not None and agreed[0] == "one" else None
        results[name] = {"assignment": text, "reference": truth, "decoded_by_order": modes, "consensus": agreed,
                         "exact": agreed == truth, "dispatched_card": chosen,
                         "correct_single_dispatch": chosen == (keys[0] if kind == "one" else None)}
    return {"scope": "Exact order-swapped intent-set retrieval against four authenticated card descriptions. "
                     "Only a consensus single-card result can dispatch on the existing protocol.",
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
