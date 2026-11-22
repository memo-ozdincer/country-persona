"""Validate request scope against verbatim action mentions before routing."""
import argparse
from itertools import batched
import json
from pathlib import Path
import re
from unittest.mock import patch

import semantic_intent as previous

HERE = previous.HERE
partner = previous.partner
GUIDE = (
    "Extract the wording that identifies each record actually requested. Quote exact contiguous spans of the "
    "assignment, one requested record per line, with no quotation marks or bullets. Preserve the actor and what "
    "they did or which position the requester asks about. Include each allowed alternative as its own line. "
    "Leave out records already held, explicitly excluded or mentioned only as background. If the wording does "
    "not identify an actionable record, return NONE. Do not explain the answer."
)
FRESH = {
    "witness/single_procedure": ("I have the sponsor's remarks already. Please locate the message that notified Council members of the completed written vote.", "one", ("council_president",)),
    "witness/single_national": ("Find the policy case Djani gave for Indonesia's draft rather than the formal notice he sent about the tally.", "one", ("indonesia_national",)),
    "witness/negative_vote": ("Get the explanation of the negative vote on the Indonesian draft. I have Russia's explanation already.", "one", ("us",)),
    "witness/both_roles": ("Retrieve both the Indonesian sponsor's position and the letter transmitting the Council result.", "all", ("indonesia_national", "council_president")),
    "witness/pair_national": ("Get the U.S. explanation of the negative vote together with Russia's explanation of the affirmative vote.", "all", ("us", "russia")),
    "witness/alternative": ("Either the explanation Russia gave for its vote or the letter reporting the written result would do.", "any", ("russia", "council_president")),
    "witness/ambiguous_actor": ("Please locate whatever Djani contributed around this vote.", "unspecified", ()),
    "witness/ambiguous_letter": ("Find the document associated with the person who chaired that month.", "unspecified", ()),
}
ALTERNATIVE = re.compile(r"\b(?:either|any one|one of|whichever)\b", re.I)
JOINT = re.compile(r"\b(?:both|together with|along with|as a separate item)\b", re.I)
ACTION = re.compile(r"\b(?:explanation|reason|grounds|position|assessment|justif\w*|argument|remarks|what .{0,40}(?:said|argued|told)|rationale)\b", re.I)
ACTORS = {
    "us": re.compile(r"\b(?:American|United States|U\.?S\.?|negative vote|no vote)\b", re.I),
    "russia": re.compile(r"\bRussia\w*\b", re.I),
    "indonesia_national": re.compile(r"\b(?:Indonesia\w*|Djani|sponsor\w*|his country)\b", re.I),
}
ROLE = re.compile(r"\b(?:national|policy|on behalf|Member States|spoke for|speaking for|his country|draft|proposal|sponsor\w*)\b", re.I)
PROCEDURE = re.compile(
    r"\b(?:result letter|official notification|certified (?:result|voting outcome)|formal (?:notice|notification|transmission)|"
    r"(?:transmit\w*|forward\w*|notif\w*|sent|informed|communicat\w*|report\w*|convey\w*)"
    r".{0,45}\b(?:members|tally|result|voting outcome|ballot))\b", re.I
)
EXCLUSION = re.compile(r"\b(?:rather than|except|leave out|leave aside|exclude|do not need|not asking for)\b", re.I)


def examples():
    return {**previous.examples(), **FRESH}


def requests():
    for name, (text, _, _) in examples().items():
        yield partner.replay.request(name, 72, GUIDE, {"assignment": text}, [])


def episode(generate):
    rows = {}
    for group in batched(requests(), 4):
        rows.update(generate(list(group)))
    return [{"family": "written-vote-witnesses", "final": rows}]


def locks():
    return {**previous.locks(), "request_witness": partner.digest(Path(__file__)),
            "operator_record": partner.digest(HERE / "operator-evidence/results.json")}


def run(directory):
    with patch.object(partner.runner, "episode", episode), patch.object(partner.runner, "locks", locks):
        partner.runner.run(Path(partner.read(partner.writer.MODEL)["model"]), directory)


def source_for(span):
    choices = set()
    procedure = PROCEDURE.search(span)
    if procedure:
        choices.add("council_president")
    if ACTION.search(span):
        choices.update(key for key in ("us", "russia") if ACTORS[key].search(span))
        if ACTORS["indonesia_national"].search(span) and ROLE.search(span):
            choices.add("indonesia_national")
    return next(iter(choices)) if len(choices) == 1 else None


def compile_intent(text, output, ended):
    if output == "NONE" and ended:
        return ("unspecified", ()), "no_witness"
    if not ended or not output:
        return None, "invalid_generation"
    spans = output.splitlines()
    if not 1 <= len(spans) <= 2 or not all(span and text.count(span) == 1 for span in spans):
        return None, "non_exact_spans"
    indexed = sorted(((text.index(span), span) for span in spans))
    if len(indexed) > 1 and indexed[0][0] + len(indexed[0][1]) > indexed[1][0]:
        return None, "overlapping_spans"
    for start, span in indexed:
        before = text[:start].rsplit(".", 1)[-1]
        if EXCLUSION.search(span) or EXCLUSION.search(before):
            return None, "excluded_scope"
    keys = [source_for(span) for _, span in indexed]
    if None in keys or len(set(keys)) != len(keys):
        return None, "unresolved_card"
    if ALTERNATIVE.search(text):
        return (("any", tuple(sorted(keys))), "verified") if len(keys) == 2 else (None, "missing_alternative")
    if JOINT.search(text) and len(keys) < 2:
        return None, "missing_joint_member"
    if len(keys) == 2:
        between = text[indexed[0][0] + len(indexed[0][1]):indexed[1][0]]
        if not (JOINT.search(text) or re.search(r"\band\b", between, re.I)):
            return None, "unresolved_connective"
        return ("all", tuple(sorted(keys))), "verified"
    return ("one", tuple(keys)), "verified"


def report(directory):
    with patch.object(partner.replay, "episode", episode), patch.object(partner.replay, "locks", locks):
        rows = partner.replay.verify(directory)
    out = {}
    for key, (assignment, kind, ids) in examples().items():
        row = rows[key]
        decision, why = compile_intent(assignment, row["output"], row["ended"])
        expected = kind, tuple(sorted(ids))
        out[key] = {"assignment": assignment, "reference": expected, "generated_spans": row["output"],
                    "decision": decision, "reason": why, "exact": expected == decision,
                    "wrong_dispatch": bool(decision and decision[0] != "unspecified" and decision != expected)}
    return {"scope": "One frozen model call proposes exact spans from the assignment. Local rules validate quotes "
                     "and the small written-vote registry. The original 24 examples are exposed development cases. "
                     "Eight additional requests were authored before this run and use the same one-docket vocabulary.",
            "trace_sha256": partner.digest(directory / "transcript.jsonl"), "records": out}


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("mode", choices=("run", "score"))
    cli.add_argument("directory", type=Path)
    args = cli.parse_args()
    if args.mode == "run":
        run(args.directory)
    else:
        print(json.dumps(report(args.directory), ensure_ascii=False, indent=2))
