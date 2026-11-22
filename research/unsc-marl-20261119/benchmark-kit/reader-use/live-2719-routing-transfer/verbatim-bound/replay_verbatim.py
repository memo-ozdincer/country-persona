"""Score a bounded extractive renderer on the exact received note sets."""
import argparse
from hashlib import sha256
from itertools import product
import json
from pathlib import Path
import re
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import live_transfer as live

SPLIT = re.compile(r"(?<=[.!?])\s+")
BUDGETS = (90, 100, 110, 120)


def note_key(note):
    raw = json.dumps(note, ensure_ascii=False, sort_keys=True).encode()
    return sha256(raw).hexdigest()[:12]


def inputs():
    prompts, paths = live.plan()
    assert paths == live.load(HERE.parent / "frozen-actions.json")
    episodes = {}
    for row in prompts:
        data = json.loads(row["messages"][1]["content"])
        notes = [*data["notes"], data["supplement"]]
        unique = {note_key(n): n for n in notes if n is not None}
        episodes[row["id"]] = list(unique.values())
    return episodes, paths


def notes_deck(episodes):
    return dict(sorted((note_key(note), {**note, "sentences": SPLIT.split(note["text"])})
                       for notes in episodes.values() for note in notes))


def evaluate(notes, lengths, labels, criteria, weights):
    text, facts, faults, selected = [], set(), [], []
    for note, length in zip(notes, lengths, strict=True):
        if not length:
            continue
        key = note_key(note)
        lines = SPLIT.split(note["text"])
        chosen = " ".join(lines[:length])
        assert note["text"].startswith(chosen)
        text.append(f"{note['desk']}: {chosen}")
        for index, row in enumerate(labels[key][:length]):
            facts.update(row["atoms"])
            if row.get("uncertain"):
                faults.append({"note": key, "sentence": index, "uncertainty": row["uncertain"]})
        selected.append({"id": key, "sentences_kept": length})
    body = "\n\n".join(text)
    met = [name for name, required in criteria.items() if set(required) <= facts]
    points = sum(weights[k] for k in met)
    return {"words": len(body.split()), "points": points, "guarded_points": points if not faults else 0,
            "source_review_passed": not faults, "uncertainties": faults, "criteria": met, "atoms": sorted(facts),
            "selected": selected, "body": body}


def round_robin(notes, sizes, budget):
    lengths = [0] * len(notes)
    remaining = budget
    while True:
        changed = False
        for index, note in enumerate(notes):
            used = lengths[index]
            if used == len(sizes[index]):
                continue
            price = sizes[index][used] + (len(note["desk"].split()) if not used else 0)
            if price <= remaining:
                remaining -= price
                lengths[index] += 1
                changed = True
        if not changed:
            return lengths


def score(episodes, paths):
    grammar = live.load(HERE / "grammar.json")
    criteria = grammar["criteria"]
    weights = {r["id"]: r["points"] for r in live.load(live.PACKET)["criteria"]}
    labels = live.load(HERE / "annotations.json")
    archive = live.load(HERE.parent / "results.json")
    deck = notes_deck(episodes)
    assert set(labels) == set(deck) and set(criteria) == set(weights)
    assert all(len(labels[k]) == len(v["sentences"]) for k, v in deck.items())
    assert all(r["span"] == sentence
               for key, value in deck.items() for r, sentence in zip(labels[key], value["sentences"], strict=True))
    assert len(episodes) == 6
    cases = {}
    for key, notes in episodes.items():
        sizes = [[len(s.split()) for s in SPLIT.split(n["text"])] for n in notes]
        full = [len(row) for row in sizes]
        all_candidates = [evaluate(notes, counts, labels, criteria, weights)
                          for counts in product(*(range(n + 1) for n in full))]
        unbounded = evaluate(notes, full, labels, criteria, weights)
        by_budget = {}
        for budget in BUDGETS:
            allowed = [r for r in all_candidates if r["words"] <= budget]
            estimate = max((r for r in allowed if r["source_review_passed"]),
                           key=lambda r: (r["points"], -r["words"]))
            assert estimate["source_review_passed"]
            literal = max((r for r in allowed if r["source_review_passed"]),
                          key=lambda r: (r["points"] - (
                              weights["U"] if "U" in r["criteria"] and grammar["literal_us_phrase"] not in r["atoms"]
                              else 0), -r["words"]))
            literal_points = literal["points"] - (
                weights["U"] if "U" in literal["criteria"] and grammar["literal_us_phrase"] not in literal["atoms"] else 0
            )
            baseline = evaluate(notes, round_robin(notes, sizes, budget), labels, criteria, weights)
            assert baseline["words"] <= budget
            by_budget[str(budget)] = {"reviewed_optimum": estimate, "round_robin": baseline,
                                      "literal_us_phrase_optimum_points": literal_points,
                                      "material_only_optimum_points": max(r["points"] for r in allowed),
                                      "eligible_prefix_combinations": len(allowed)}
        all_source_optimum = max((r for r in all_candidates if r["source_review_passed"]),
                                 key=lambda r: (r["points"], -r["words"]))
        cases[key] = {"all_unique_notes": unbounded, "unbounded_reviewed_optimum": all_source_optimum,
                      "budget": by_budget}
    compare = {}
    for world, arms in paths.items():
        compare[world] = {}
        for name, route in arms.items():
            key = route["generation"]
            observed = archive["worlds"][world][name]
            selected = cases[key]["budget"]["90"]
            compare[world][name] = {"generation": key, "generated_points": observed["points"],
                                    "generated_release": observed["release"],
                                    "round_robin_guarded_points": selected["round_robin"]["guarded_points"],
                                    "extractive_guarded_points": selected["reviewed_optimum"]["guarded_points"]}
    return {"cases": cases, "worlds_at_90_words": compare,
            "sha256": {p.name: live.runner.digest(p) for p in (
                HERE / "protocol.json", HERE / "grammar.json", HERE / "annotations.json",
                HERE.parent / "frozen-actions.json", HERE.parent / "results.json")}}


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("mode", choices=("deck", "score"))
    cases, table = inputs()
    out = notes_deck(cases) if cli.parse_args().mode == "deck" else score(cases, table)
    print(json.dumps(out, ensure_ascii=False, indent=2))
