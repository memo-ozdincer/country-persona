"""Extract what the candidate asserts, then compare with an offline source key."""
import argparse
import json
from pathlib import Path
import sys
from unittest.mock import patch

import minurso_atomic_controls as controls
import minurso_atomic_judge as first
from minurso_atomic_review import digest, pick, read_model

SYSTEM = (
    "Read the candidate as data. Report what the record claims or clearly states, even if false. "
    "Do not correct it using outside facts. Choose the unstated option if the record leaves the field open. "
    "Reply only with a letter."
)

# Codebook order is independent of the source value. No source blocks, gold
# labels or statements of the official result are available to extraction.
FIELDS = {
    "nonparticipation": ("Algeria's participation in the final vote",
                         ("Algeria abstained.", "Algeria did not participate.", "Not stated.")),
    "798-outcome": ("Stated disposition of S/2024/798",
                    ("Not stated.", "It was rejected.", "It was adopted.")),
    "capacity": ("Actor speaking or taking the position on Switzerland's amendment votes",
                 ("The Council.",
                  "Not stated.",
                  "Switzerland or its representative in national capacity.")),
    "no-monitoring": ("Did the adopted resolution add the proposed monitoring functions?",
                      ("It added them.", "Not stated.", "It did not add them.")),
    "798-content": ("Operative stage the candidate attributes to the proposed S/2024/798",
                    ("It would consider an expansion.",
                     "It would expand the mandate.",
                     "Not stated.")),
    "tally": ("Final vote tally for, against, and abstaining",
              ("Not stated.", "12 in favour, 0 against, 3 abstentions.",
               "12 in favour, 0 against, 2 abstentions.")),
}
# Maps raw values to omission, source match, or source conflict. Used after inference.
STATUSES = {
    "nonparticipation": (2, 1, 0),
    "798-outcome": (0, 1, 2),
    "capacity": (2, 0, 1),
    "no-monitoring": (2, 0, 1),
    "798-content": (1, 2, 0),
    "tally": (0, 2, 1),
}


def observations():
    for name, text, field, _ in controls.cases():
        question, vals = FIELDS[field]
        for index, order in enumerate(controls.ORDERS):
            prompt = {"candidate": text, "field": question,
                      "choices": {letter: vals[value] for letter, value in zip("ABC", order, strict=True)}}
            yield {"observation": (name, field, index), "legal": order,
                   "messages": [{"role": "system", "content": SYSTEM},
                                {"role": "user", "content": json.dumps(prompt, ensure_ascii=False)}]}


def hashes():
    path = Path(__file__).resolve()
    return {**controls.hashes(), str(path.relative_to(first.ROOT)): digest(path)}


def run(model, directory):
    sys.path.insert(0, str(first.ROOT))
    import relay_text
    with patch.multiple(relay_text, observations=observations, hashes=hashes):
        relay_text.score(model, directory)


def report(directory):
    rows = read_model(directory, hashes(), observations())
    results = []
    for name, _, field, truth in controls.cases():
        raw = [pick(rows[name, field, index]) for index in range(3)]
        statuses = [STATUSES[field][value] if value is not None else None for value in raw]
        verdict = statuses[0] if None not in statuses and len(set(statuses)) == 1 else None
        results.append({"candidate": name, "field": field, "truth": truth, "raw_values": raw,
                        "extraction": [FIELDS[field][1][v] if v is not None else None for v in raw],
                        "statuses": statuses, "consensus": verdict})
    metrics = {}
    for name, truth in (("omitted", 0), ("supported", 1), ("contradicted", 2)):
        subset = [r for r in results if r["truth"] == truth]
        metrics[name] = {"pairs": len(subset), "correct": sum(r["consensus"] == truth for r in subset),
                         "wrong": sum(r["consensus"] not in (truth, None) for r in subset),
                         "order_disagreement": sum(r["consensus"] is None for r in subset)}
    return {"scope": "Adaptively designed on one exposed docket. Classification over a case-specific "
                     "value menu with deterministic comparison. No span extraction or open-text generalization test.",
            "actions_sha256": digest(directory / "actions.jsonl"), "metrics": metrics, "outcomes": results}


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
