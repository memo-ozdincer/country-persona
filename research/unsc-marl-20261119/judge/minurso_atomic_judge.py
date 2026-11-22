"""Check claim coverage and errors in a controlled MINURSO panel."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
AUDIT = ROOT / "benchmark-kit/validity-audit"
DOSSIER = AUDIT / "source-record-minurso.json"
ANCHORS = AUDIT / "source-record-minurso-anchors.json"
RUBRIC = HERE / "minurso-atomic-rubric.json"
SELECTED = ("nonparticipation", "798-outcome", "capacity", "no-monitoring", "798-content")
OPTIONS = (
    "The candidate leaves the tested fact unstated or incomplete.",
    "The candidate states the complete tested fact accurately.",
    "The candidate contradicts or materially changes the tested fact.",
)
ORDERS = ((0, 1, 2), (2, 1, 0))
SYSTEM = (
    "Evaluate one required fact in the candidate record using the accompanying evidence. "
    "Accept accurate paraphrases. Choose incomplete if the candidate omits a required part. "
    "Choose contradicts if it states an incompatible vote, outcome, actor, role, or degree of authority. "
    "Grade only this fact even if another part of the record is wrong. Reply with the choice letter only."
)


def rubric():
    groups = json.loads(RUBRIC.read_text())["groups"]
    assert all(sum(p["weight"] for p in g["parts"]) == 14 for g in groups)
    parts = {p["id"]: p for g in groups for p in g["parts"]}
    assert len(parts) == sum(len(g["parts"]) for g in groups)
    return groups, parts


def fixtures():
    cases = json.loads(ANCHORS.read_text())
    negatives = {"anchor-nonparticipation": "nonparticipation", "anchor-amendment": "798-outcome",
                 "anchor-capacity": "capacity", "anchor-authority": "no-monitoring"}
    for row in cases:
        p = row["packet"]
        yield p["id"], p["answer"], {negatives[p["id"]]: 2} if p["id"] in negatives else {}
    full = cases[0]["packet"]["answer"]
    omitted = " Algeria did not participate"
    changed = "to consider expanding MINURSO for rights monitoring"
    assert full.count(omitted) == full.count(changed) == 1
    yield "anchor-omitted", full.replace(omitted, ""), {"nonparticipation": 0}
    yield "anchor-approval-scope", full.replace(changed, "to expand MINURSO for rights monitoring"), {"798-content": 2}


def observations():
    _, parts = rubric()
    blocks = {r["id"]: r["text"] for r in json.loads(ANCHORS.read_text())[0]["packet"]["evidence"]}
    for fixture, text, _ in fixtures():
        for criterion in SELECTED:
            part = parts[criterion]
            for i, order in enumerate(ORDERS):
                body = {"evidence": {k: blocks[k] for k in part["blocks"]}, "candidate": text,
                        "tested_fact": part["criterion"],
                        "choices": {k: OPTIONS[v] for k, v in zip("ABC", order, strict=True)}}
                yield {"observation": (fixture, criterion, i), "legal": order, "messages": [
                    {"role": "system", "content": SYSTEM},
                    {"role": "user", "content": json.dumps(body, ensure_ascii=False)},
                ]}


def hashes():
    files = (Path(__file__).resolve(), ROOT / "relay_text.py", DOSSIER, ANCHORS, RUBRIC)
    return {str(f.relative_to(ROOT)): sha256(f.read_bytes()).hexdigest() for f in files}


def run(model, directory):
    import sys

    sys.path.insert(0, str(ROOT))
    import relay_text
    with patch.multiple(relay_text, observations=observations, hashes=hashes):
        relay_text.score(model, directory)


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("directory", type=Path)
    cli.add_argument("--model", type=Path, required=True)
    args = cli.parse_args()
    run(args.model, args.directory)
