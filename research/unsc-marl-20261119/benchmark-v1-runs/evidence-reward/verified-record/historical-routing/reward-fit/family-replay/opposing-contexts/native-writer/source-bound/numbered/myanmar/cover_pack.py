"""Review a scope-preserving budget allocator on the same sealed selections."""
import argparse
from functools import partial
from itertools import product
import json
from unittest.mock import patch

import evaluate_transfer as q

t = q.t
base = t.pack


def preserve(mask, choices, deck, *, preserve_intact=False):
    public = base(0, choices, deck)["text"]
    candidates = [(role, card, len(ids) - i) for bit, (role, ids) in zip(t.n.BITS[1:], choices.items())
                  if mask & bit for i, card in enumerate(ids)]
    winner = None
    for bits in product((False, True), repeat=len(candidates)):
        chosen = {k: [] for k in t.ROLES}
        weight = 0
        for bit, (role, key, value) in zip(bits, candidates):
            if bit:
                chosen[role].append(key)
                weight += value
        india, chair = set(chosen["india"]), set(chosen["chair"])
        if ("8" in india and "7" not in india
                or "3" in chair and "6" not in chair
                or "1" in chair and not {"6", "3"} <= chair):
            continue
        overlap = t.overlaps(chosen)
        paragraphs = [public]
        for role, ids in chosen.items():
            if ids:
                refs = sorted((deck["cards"][role][key] for key in ids), key=lambda row: row["start"])
                paragraphs.append(t.LABELS[role] + " — " + " ".join("“" + row["text"] + "”" for row in refs))
        if overlap:
            paragraphs.append("Both delegations addressed regional concerns, while their votes differed.")
        text = "\n\n".join(paragraphs)
        words = len(text.split())
        if words > t.n.LIMIT:
            continue
        intact = sum(t.enough(role, set(ids)) for role, ids in chosen.items()) if preserve_intact else 0
        order = (intact, sum(bool(x) for x in chosen.values()), overlap, weight, words)
        if winner is None or order > winner[0]:
            winner = order, {"text": text, "words": words, "used": {k: sorted(v) for k, v in chosen.items()}}
    assert winner is not None
    return winner[1]


def grades(preserve_intact=False):
    with patch.object(t, "pack", partial(preserve, preserve_intact=preserve_intact)):
        return q.grade()


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("mode", choices=("grades", "replay"))
    cli.add_argument("--intact", action="store_true", help="Protect complete local reasons before comparison")
    args = cli.parse_args()
    label = "intact" if args.intact else "protected"
    t.e.emit(grades(args.intact) if args.mode == "grades" else
             q.replay(json.loads((t.HERE / f"{label}-grades.json").read_text())))
