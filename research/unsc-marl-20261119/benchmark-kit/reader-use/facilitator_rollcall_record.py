"""Compose the official and delegate parts of an explicitly bound vote record."""
import argparse
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import re

import facilitator_verified_brief as study
import facilitator_verified_brief_score as quality

ADOPTED = re.compile(r"^The Security Council adopted resolution (\d{1,4} \(\d{4}\)) by ")


def compose(payload):
    """Build an answer from source lines when both role claims refer to the Council's recorded roll call."""
    assertions, sources, excerpts = (payload[key] for key in ("assertions", "sources", "candidate_excerpts"))
    council = ADOPTED.match(sources["S0"])
    if council is None or assertions.keys() != excerpts.keys() or tuple(assertions) != ("S1", "S2"):
        return None
    verdicts = []
    for sid, assertion in assertions.items():
        asked = study.vote.typed_vote(assertion)
        if asked is None or asked[1] != council.group(1):
            return None
        outcome = study.vote.check(assertion, excerpts[sid], sources[sid])
        if outcome is None:
            return None
        verdicts.append(outcome)
    heading = "revise" if "conflict" in verdicts else "retain"
    spans = {"council": f"{sources['S0']} [S0]", "s1": f"{excerpts['S1']} [S1]", "s2": f"{excerpts['S2']} [S2]"}
    body = " ".join(spans.values())
    if len(body.split()) > 75 or "\n" in body or "|" in body:
        return None
    return f"{heading} | {body}", spans


def evaluation(directory):
    archive = directory / "results.json"
    baseline = json.loads(archive.read_text())
    trace = directory / "transcript.jsonl"
    rows = {r["id"]: r for r in map(json.loads, trace.read_text().splitlines())}
    output = {}
    totals = Counter()
    for panel, _, item, _ in study.panels():
        key = f"{panel}/hybrid/final"
        payload = json.loads(rows[key]["messages"][1]["content"])
        rendered = compose(payload)
        if rendered is None:
            grade = baseline["finals"][key]
        else:
            text, marks = rendered
            grade = quality.grade({"output": text, "ended": True}, marks | {"issue": "", "reason": ""},
                                  item["expected"])
        output[panel] = {"composed": rendered is not None, **grade}
        totals.update({"records": 1, "composed": rendered is not None, "strict": grade["strict"],
                       "points": grade["points"], "disposition_right": grade["disposition"] == grade["expected"]})
    return {"scope": "Post hoc pipeline control. The composer uses the public Council card and binding of both vote "
                     "witnesses to the queried actors and resolution. Other claims use the archived hybrid writer. "
                     "No new language model calls. Scoring uses the same 70 point final contract.",
            "summary": totals, "records": output,
            "sha256": {p.name: sha256(p.read_bytes()).hexdigest() for p in (Path(__file__), archive, trace)}}


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("evidence", type=Path)
    print(json.dumps(evaluation(p.parse_args().evidence), indent=2))
