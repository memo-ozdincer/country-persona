"""Preserve qualified claims and pack source spans under one global cap."""
import argparse
from itertools import product
import json
from unittest.mock import patch

import numbered as w
import numbered_eval as evals

base = w.records


def pack(mask, selected, deck, public):
    candidates = [(role, i, len(ids) - offset) for bit, (role, ids) in zip(w.n.BITS[1:], selected.items())
                  if mask & bit for offset, i in enumerate(ids)]
    winner = None
    for included in product((False, True), repeat=len(candidates)):
        subset = {role: [] for role in selected}
        for keep, (role, i, rank) in zip(included, candidates):
            if keep:
                subset[role].append(i)
        br = set(subset["brazil"])
        if ("8" in br) != ("6" in br):
            continue
        paragraphs = [public]
        for role, ids in subset.items():
            if ids:
                units = sorted((deck["cards"][role][i] for i in ids), key=lambda row: row["start"])
                paragraphs.append(role.title() + " — " + " ".join("“" + r["text"] + "”" for r in units))
        if all(ids <= set(subset[role]) for role, ids in w.COMPARE.items()):
            paragraphs.append("Brazil and China backed UNIFIL but differed over accommodation of Lebanese concerns.")
        summary = "\n\n".join(paragraphs)
        words = len(summary.split())
        if words > w.n.LIMIT:
            continue
        merit = (sum(bool(ids) for ids in subset.values()),
                 sum(r for used, (_, _, r) in zip(included, candidates) if used),
                 words)
        if winner is None or merit > winner[0]:
            winner = merit, {"text": summary, "used": subset}
    assert winner is not None
    return winner[1]


def grade():
    data = base()
    deck = w.plan()
    public = data["records"]["native"][0]["text"]
    native = {role: grade[0] for role, grade in data["selection"].items()}
    whole = {role: list(items) for role, items in w.MENUS.items()}
    first = {role: ids[:1] for role, ids in whole.items()}
    data["records"] = {arm: {mask: pack(mask, chosen, deck, public) for mask in range(8)}
                       for arm, chosen in (("native", native), ("all_passages", whole), ("first_menu_item", first))}
    with patch.object(w, "records", return_value=data):
        return evals.grade_records()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("grades", "replay"))
    mode = parser.parse_args().mode
    w.e.emit(grade() if mode == "grades" else evals.replay(json.loads((w.HERE / "packed-grades.json").read_text())))
