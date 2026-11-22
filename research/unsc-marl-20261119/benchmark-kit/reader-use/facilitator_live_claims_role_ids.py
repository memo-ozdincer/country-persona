"""Repair capacity witness binding by selecting exact existing sentence IDs."""
import argparse
import json
from pathlib import Path
import re
from unittest.mock import patch

import facilitator_live_claims as original
import facilitator_live_claims_score as scored

HERE = original.HERE
FAMILY = "facilitator-live-claims-role-ids"
EVIDENCE = original.EVIDENCE / "role-ids"
TASK = (
    "The required record has two facts: first, the Council President announced adoption; "
    "second, India's representative separately explained the national abstention. "
    "Return two supplied sentence IDs in order, separated by one space, that establish those facts. "
    "If either fact or the distinction in capacity is missing, return NONE. Do not add any words."
)


def cases():
    checks = original.items(original.old_rows())
    matched = {key: row["evidence"] for key, row in checks.items() if "/role/" in key}
    matched["control/india-national-only"] = original.previous.dossier("myanmar")[1]["india"]
    for key, source in matched.items():
        sentences = re.split(r"(?<=[.!?])\s+", source)
        yield key, {chr(65 + i): value for i, value in enumerate(sentences)}


def requests():
    for key, sentences in cases():
        yield original.previous.previous.prompt(key, 10, TASK, {"sentences": sentences})


def pins():
    directory = original.EVIDENCE
    paths = (Path(__file__).resolve(), Path(original.__file__), Path(scored.__file__),
             Path(original.RUNNER.__file__), directory / "launch.json", directory / "complete.json",
             directory / "transcript.jsonl", directory / "marks.json")
    return {str(p.relative_to(original.previous.ROOT)): original.RUNNER.digest(p) for p in paths}


def episode(generate):
    return [{"family": FAMILY, "final": generate(list(requests()))}]


def verify(directory):
    base = original.previous.previous.common.reused.previous.prior
    with patch.multiple(base, local=requests, audits=lambda rows: (), syntheses=lambda rows: (),
                        pins=pins, FAMILY=FAMILY):
        return base.read(directory)


def score(directory):
    observed = verify(directory)
    old = original.verify(original.EVIDENCE)
    marks = json.loads((original.EVIDENCE / "marks.json").read_text())
    reviewed = json.loads((directory / "review.json").read_text())
    assert reviewed.keys() == observed.keys()
    outputs = {}
    for key, options in cases():
        reply = observed[key]
        answer = reply["output"].split()
        valid = reply["ended"] and len(answer) == 2 and all(label in options for label in answer)
        spans = [options[label] for label in answer] if valid else []
        entry = reviewed[key]
        assert entry["supported"] in ("met", "unmet", "uncertain") and entry["reason"].strip()
        if entry["supported"] == "met":
            assert valid and not key.startswith("control/")
            text = " ".join(spans)
            view = original.items(original.old_rows())[key]["evidence"]
            assert text in view
            old[key] = {**old[key], "output": text, "ended": True}
            marks[key] = {"supported": "met", "span": text, "reason": entry["reason"]}
        outputs[key] = {"output": reply["output"], "selected": spans, **entry}
    return {"scope": "Post hoc sentence-label interface for failed role witnesses. Preserve the same views and all "
                     "other witness grades. The joined exact evidence must occur verbatim to enter the record.",
            "decisions": outputs, "reassembled": scored.run(old, marks)}


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode", choices=("run", "score"))
    p.add_argument("directory", type=Path)
    p.add_argument("--model", type=Path)
    args = p.parse_args()
    if args.mode == "score":
        print(json.dumps(score(args.directory), indent=2, ensure_ascii=False))
    else:
        with patch.multiple(original.RUNNER, episode=episode, locks=pins):
            original.RUNNER.run(args.model, args.directory)
