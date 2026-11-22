"""Measure the same source judgments under old and balanced letter assignments."""
from collections import Counter, defaultdict
import json
from pathlib import Path

import numpy as np

import balance as study

HERE, e, team = study.HERE, study.e, study.team


def one(scores):
    _, label = team.mapped({"legal": [0, 1, 2], "scores": scores})
    return label


def votes(group):
    if len(set(group)) == 1:
        return group[0]
    return 2


def majority(group):
    count = Counter(group)
    lead, total = count.most_common(1)[0]
    return lead if total > len(group) / 2 else 2


def decode(rows):
    scores, decisions = zip(*(team.mapped(row) for row in rows), strict=True)
    def pool(indices):
        return one(np.mean([scores[i] for i in indices], axis=0))
    return ({
        "identity": decisions[0], "reversed": decisions[1], "cycle_one": decisions[2], "cycle_two": decisions[3],
        "old_agreement": votes(decisions[:2]), "old_pooled": pool((0, 1)),
        "cycles_agreement": votes(decisions[2:]), "cycles_pooled": pool((2, 3)),
        "balanced_unanimous": votes([decisions[i] for i in (0, 2, 3)]),
        "balanced_majority": majority([decisions[i] for i in (0, 2, 3)]),
        "balanced_pooled": pool((0, 2, 3)),
    }, decisions)


def statistics(rows):
    names = tuple(rows[0]["decisions"])
    return {arm: {
        "correct": sum(r["decisions"][arm] == r["truth"] for r in rows),
        "correct_decisive": sum(r["decisions"][arm] == r["truth"] != "unknown" for r in rows),
        "wrong_decisive": sum(r["decisions"][arm] not in (r["truth"], "unknown") for r in rows),
        "deferred": sum(r["decisions"][arm] == "unknown" for r in rows),
        "errors": [r["case"] for r in rows if r["decisions"][arm] not in (r["truth"], "unknown")],
    } for arm in names}


def run():
    study.lock()
    fresh = study.OUT / "calls.jsonl"
    assert team.pin(fresh) == e.read(HERE / "verified.json")["evidence_sha256"]["calls.jsonl"]
    rows = study.old_rows() + list(map(json.loads, fresh.read_text().splitlines()))
    prompts = defaultdict(dict)
    for row in rows:
        group, key, position = row["observation"]
        assert position not in prompts[group, key]
        prompts[group, key][position] = row
    archive = e.read(team.ARCHIVE / "results.json")["decisions"]
    myanmar = {row["id"]: row["expected"] for row in e.read(study.MYANMAR / "plan.json")["fixtures"]}
    results = []
    for (group, key), values in prompts.items():
        assert set(values) == set(range(4))
        observed = [values[i] for i in range(4)]
        pred, individual = decode(observed)
        expected = archive[f"routed/{key}"]["expected"] if group == "routed" else myanmar[key]
        if group == "routed":
            stable = archive[f"routed/{key}"]["stable_relation"]
            assert team.LABELS[pred["old_agreement"]] == stable
        letters = ["".join("ABC"[j] for j, score in enumerate(r["scores"]) if score == max(r["scores"]))
                   for r in observed]
        results.append({"case": key, "cohort": "archive" if group == "routed" else "myanmar",
                        "truth": expected, "physical_letters": letters,
                        "mapped_labels": [team.LABELS[i] for i in individual],
                        "decisions": {k: team.LABELS[v] for k, v in pred.items()}})
    grouped = {cohort: [row for row in results if row["cohort"] == cohort] for cohort in ("archive", "myanmar")}
    assert {k: len(v) for k, v in grouped.items()} == {"archive": 19, "myanmar": 8}
    cohort_stats = {k: statistics(v) for k, v in grouped.items()}
    differences = {}
    for cohort, subset in grouped.items():
        differences[cohort] = {}
        for arm in ("cycles_agreement", "cycles_pooled", "balanced_unanimous", "balanced_majority", "balanced_pooled"):
            comparator = "old_pooled" if arm.endswith("pooled") else "old_agreement"
            differences[cohort][arm] = {
                "comparator": comparator,
                "fixes": [r["case"] for r in subset if r["decisions"][comparator] != r["truth"] == r["decisions"][arm]],
                "regressions": [r["case"] for r in subset if r["decisions"][comparator] == r["truth"] != r["decisions"][arm]],
            }
    return {"scores": cohort_stats, "paired_changes": differences, "decisions": results,
            "sha256": {p.name: team.pin(p) for p in (Path(__file__), HERE / "verified.json", HERE / "plan.json")}}


if __name__ == "__main__":
    e.emit(run())
