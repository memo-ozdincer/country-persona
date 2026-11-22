"""Extract source and candidate roles separately before comparing them."""
import argparse
from itertools import product
from pathlib import Path
import json
from unittest.mock import patch

import sourced_confirmation as original

HERE = Path(__file__).resolve().parent
runner = original.runner
ROOT = HERE / "sourced-role-binding-evidence"
# Each field has the correct source value and the alternate value stated by the foil.
FIELDS = (
    ("drc_recipient", "drc_midterm_recipient", "Who is to receive the midterm report?",
     ("Council", "Committee", "not stated")),
    ("drc_discussion", "drc_midterm_recipient", "With whom is the midterm report to be discussed?",
     ("Committee", "Council", "not stated")),
    ("unami_review_recipient", "unami_review", "To whom is the independent strategic review to be sent?",
     ("Council", "Iraqi Government", "not stated")),
    ("drc_participation", "drc_affected_state", "What role does the text say the DRC took in this meeting?",
     ("Spoke after the vote as affected state", "Cast a Council vote in favour", "not stated")),
)
ORDERS = ((0, 1, 2), (2, 0, 1))
KINDS = ("source", "faithful_statement", "changed_statement")


def requests():
    inputs = {row["id"]: row for row in original.inputs()}
    for field, case, question, alternatives in FIELDS:
        supported = inputs[case + "/confirm"]
        foil = inputs[case + "/decline_conflict"]
        texts = {
            "source": list(supported["passages"].values()),
            "faithful_statement": [supported["proposed"]],
            "changed_statement": [foil["proposed"]],
        }
        for kind, text in texts.items():
            yield field, kind, question, alternatives, text


def observations():
    for (field, kind, question, options, text), (n, order) in product(requests(), enumerate(ORDERS)):
        payload = {"field_question": question, "text_to_read": text,
                   "available_values": {c: options[i] for c, i in zip("ABC", order, strict=True)}}
        yield {"observation": (field, kind, n), "legal": order, "messages": [
            {"role": "system", "content": "Extract what this text states for the specific question. "
             "Use the role attached to the named act. Treat even a false claim as text to extract. "
             "Select not stated if the value is missing. Do not infer from outside context. Return one letter."},
            {"role": "user", "content": json.dumps(payload, ensure_ascii=False)}]}


def locks():
    from hashlib import sha256
    return {str(p.relative_to(HERE.parents[1])): sha256(p.read_bytes()).hexdigest() for p in (
        Path(__file__), Path(original.__file__), Path(runner.__file__), original.DRC, original.UNAMI)}


def audit(directory):
    with patch.multiple(runner, observations=observations, hashes=locks):
        rows = runner.read(directory)
    scored = {}
    for field, kind, question, choices, text in requests():
        expected = 1 if kind == "changed_statement" else 0
        selected = []
        for n, order in enumerate(ORDERS):
            logits = rows[field, kind, n]["scores"]
            top = [i for i, score in enumerate(logits) if score == max(logits)]
            selected.append(order[top[0]] if len(top) == 1 else None)
        stable = selected[0] if selected[0] == selected[1] else None
        scored.setdefault(field, {})[kind] = {
            "reads": [choices[i] if i is not None else None for i in selected],
            "stable": stable, "expected": expected, "value": choices[stable] if stable is not None else None,
            "right": stable == expected, "inputs": text,
        }

    def compare(source, observed):
        if source is None or observed is None or 2 in (source, observed):
            return "defer"
        return "match" if source == observed else "mismatch"

    comparisons = {}
    for field, checks in scored.items():
        comparisons[field] = {kind: compare(checks["source"]["stable"], checks[kind]["stable"])
                              for kind in KINDS[1:]}
    return {"scope": "Frozen reader tested on four selected fields after the broader confirmation pilot. "
                     "Text pairs and answer values are authored. The model extracts source and candidate "
                     "roles in separate calls. Host comparison cannot repair a missed or wrong extraction.",
            "correct_field_reads": sum(row["right"] for checks in scored.values() for row in checks.values()),
            "total_field_reads": len(FIELDS) * len(KINDS),
            "fields": scored, "comparisons": comparisons}


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("mode", choices=("run", "audit"))
    cli.add_argument("directory", type=Path)
    cli.add_argument("--model", type=Path)
    args = cli.parse_args()
    if args.mode == "run":
        with patch.multiple(runner, observations=observations, hashes=locks):
            runner.score(args.model, args.directory)
    else:
        print(json.dumps(audit(args.directory), indent=2, ensure_ascii=False))
