"""Recover the Russia field by selecting the stated extension horizon."""
import argparse
import json
from pathlib import Path
import sys
from unittest.mock import patch

import mali_source_request_reader as base

SYSTEM = (
    "Select the exact words that state the proposed length or finality of an extension. "
    "Words about dissolving the Panel of Experts do not establish the extension horizon. "
    "Select 'No explicit extension horizon' when the passage does not say. Return exactly one choice letter."
)
KEY = "making this the final extension of the regime"
COUNTER = "making this the first of several extensions of the regime"
CONTROL = "dissolving the Panel of Experts"


def probes():
    for field, variant, text, _ in base.entries():
        if field != 2:
            continue
        found = KEY if KEY in text else COUNTER if COUNTER in text else None
        assert CONTROL in text
        yield variant, text, (None, CONTROL, found) if found else (None, CONTROL)


def observations():
    for variant, text, opts in probes():
        for k in range(len(opts)):
            order = tuple((k + i) % len(opts) for i in range(len(opts)))
            payload = {"passage": text,
                       "choices": {c: opts[i] or "No explicit extension horizon"
                                   for c, i in zip("ABC"[:len(opts)], order, strict=True)}}
            yield {"observation": (variant, k), "legal": order, "messages": [
                {"role": "system", "content": SYSTEM},
                {"role": "user", "content": json.dumps(payload, ensure_ascii=False)}]}


def hashes():
    return {**base.hashes(), Path(__file__).name: base.digest(Path(__file__))}


def run(model, directory):
    sys.path.insert(0, str(base.ROOT))
    import relay_text
    with patch.multiple(relay_text, observations=observations, hashes=hashes):
        relay_text.score(model, directory)


def report(directory, old, policy):
    from mali_source_request_replay import report as replay

    rows = base.read_model(directory, hashes(), observations())
    ratings = {}
    for variant, text, options in probes():
        votes = [base.pick(rows[variant, i]) for i in range(len(options))]
        expected = 2 if len(options) == 3 else 0
        consistent = votes[0] if None not in votes and len(set(votes)) == 1 else None
        span = options[consistent] if consistent is not None else None
        assert span is None or span in text
        matches = span == KEY and CONTROL in text and text.startswith(("Russia said", "It proposed"))
        ratings[variant] = {"positions": votes, "expected": expected, "agreed_span": span,
                            "qualified": bool(matches)}

    report = base.report(old)
    readings = []
    for row in report["readings"]:
        if row["field"] == 2:
            row = {**row, "new_term_probe": ratings[row["variant"]],
                   "agreed_role": 2 if ratings[row["variant"]]["qualified"] else 0}
        readings.append(row)
    changed = {**report, "readings": readings,
               "term_probe_actions_sha256": base.digest(directory / "actions.jsonl")}
    with patch("mali_source_request_replay.readings_report", return_value=changed):
        integrated = replay(old, policy)
    integrated["scope"] = (
        "Adaptive developed Mali replay. The Russia slot uses a new explicit-horizon check on four passages "
        "from the known Western Sahara/DPRK-to-Mali transfer evaluation. The two other readers and learned "
        "policy remain fixed. Source and statement ownership are taken as given for this focused qualifier test."
    )
    integrated["term_probe"] = ratings
    return integrated


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("mode", choices=("run", "report"))
    cli.add_argument("directory", type=Path)
    cli.add_argument("--model", type=Path)
    cli.add_argument("--old", type=Path)
    cli.add_argument("--policy", type=Path)
    args = cli.parse_args()
    if args.mode == "run":
        if args.model is None:
            cli.error("run requires --model")
        run(args.model, args.directory)
    else:
        if args.old is None or args.policy is None:
            cli.error("report requires --old and --policy")
        print(json.dumps(report(args.directory, args.old, args.policy), ensure_ascii=False, indent=2))
