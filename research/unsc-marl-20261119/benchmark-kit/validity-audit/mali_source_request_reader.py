"""Check whether a frozen reader can identify the three evidence fields in prose."""
import argparse
import json
from pathlib import Path
import sys
from unittest.mock import patch

from source_request_cases import cases, hashes as case_hashes, ROOT
from source_record_run import digest

sys.path.insert(0, str(ROOT / "judge"))
from minurso_atomic_review import pick, read_model
sys.path.pop(0)

REQUIREMENTS = (
    "The passage establishes none of the three complete evidence fields.",
    "The France–UAE co-penholders sought an extension supporting both implementation of the peace agreement and an orderly drawdown.",
    "Russia sought both dissolution of the Panel of Experts and a final extension of the existing sanctions regime.",
    "France regretted the veto and said the Council members had not discussed Russia's separate draft.",
)
SYSTEM = (
    "Classify this single passage for a historical evidence request. Select the one entire claim actually supported, "
    "or none if material details are omitted or reversed. Do not infer a field from the country name, real-world "
    "history or a related policy. Use only the supplied passage. Reply with a single letter."
)
REMOVALS = (
    " and an orderly drawdown",
    " and making this the final extension of the regime",
    " and said Russia's separate proposal had not been discussed by Council members",
)
REVERSALS = (
    ("support implementation of the peace agreement", "delay implementation of the peace agreement"),
    ("the final extension of the regime", "the first of several extensions of the regime"),
    ("had not been discussed by Council members", "had been discussed by all Council members"),
)


def entries():
    for s, item in enumerate(cases()["mali"]["fields"], 1):
        text = item["evidence"][0]["quote"]
        first, tail = text.split(". ", 1)
        partial = REMOVALS[s-1]
        old, new = REVERSALS[s-1]
        assert text.count(partial) == text.count(old) == 1
        for variant, passage in [
            ("full", text), ("reordered", f"{tail} {first}."),
            ("missing", text.replace(partial, "")), ("reversed", text.replace(old, new)),
        ]:
            yield s, variant, passage, s if variant in ("full", "reordered") else 0


def observations():
    for field, variant, passage, _ in entries():
        for r in range(4):
            order = tuple((r + i) % 4 for i in range(4))
            task = {"passage": passage,
                    "choices": {letter: REQUIREMENTS[i] for letter, i in zip("ABCD", order, strict=True)}}
            yield {"observation": (field, variant, r), "legal": order, "messages": [
                {"role": "system", "content": SYSTEM},
                {"role": "user", "content": json.dumps(task, ensure_ascii=False)},
            ]}


def hashes():
    return {**case_hashes(), str(Path(__file__).resolve().relative_to(ROOT)): digest(Path(__file__)),
            "relay_text.py": digest(ROOT / "relay_text.py")}


def run(model, directory):
    sys.path.insert(0, str(ROOT))
    import relay_text
    with patch.multiple(relay_text, observations=observations, hashes=hashes):
        relay_text.score(model, directory)


def report(directory):
    rows = read_model(directory, hashes(), observations())
    decisions = []
    for field, variant, _, truth in entries():
        labels = [pick(rows[field, variant, index]) for index in range(4)]
        found = labels[0] if None not in labels and len(set(labels)) == 1 else None
        decisions.append({"field": field, "variant": variant, "truth": truth, "decisions": labels, "agreed_role": found})
    return {"scope": "Source-backed Mali prose and authored controlled edits on three requested fields. "
                     "Each field visits every letter. No weights are updated.",
            "actions_sha256": digest(directory / "actions.jsonl"), "readings": decisions}


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("mode", choices=("run", "report"))
    cli.add_argument("directory", type=Path)
    cli.add_argument("--model", type=Path)
    args = cli.parse_args()
    if args.mode == "run":
        if args.model is None:
            cli.error("run requires --model")
        run(args.model, args.directory)
    else:
        print(json.dumps(report(args.directory), ensure_ascii=False, indent=2))
