"""Score judge decisions and replay shared terminal reward calibration."""
import json
import sys

import numpy as np

from collect_judgments import HERE, RUNS, fixtures, prior, read, team

PARTNER = RUNS / "partner-conditioned-calibration"
sys.path.insert(0, str(PARTNER))
import partner_fit as partner

METHODS = ("ab", "ba", "mean", "agreement")


def judged_rows():
    outputs = read(HERE / "verified.json")["outputs"]
    rows = {}
    for key, case in fixtures().items():
        margins = {}
        for index, mapping in prior.MAPPINGS.items():
            scores = outputs[f"{key}/{index}"]["logits"]
            met = next(letter for letter, action in mapping.items() if action == "process")
            unmet = next(letter for letter, action in mapping.items() if action == "fund")
            margins[index] = scores[met] - scores[unmet]
        choices = {key: value > 0 for key, value in margins.items()}
        rows[key] = {"met": case["met"], "weight": case["weight"], "mutation": case["mutation"],
                     "margins": margins | {"mean": sum(margins.values()) / 2},
                     "judgments": choices | {"mean": sum(margins.values()) > 0,
                                            "agreement": all(choices.values())}}
    assert len(outputs) == 2 * len(rows)
    return rows


def summarize(rows):
    output = {}
    for method in METHODS:
        good = sum(r["met"] for r in rows)
        bad = len(rows) - good
        kept = sum(r["met"] and r["judgments"][method] for r in rows)
        added = sum(not r["met"] and r["judgments"][method] for r in rows)
        output[method] = {"true_accepted": kept, "true": good, "false_accepted": added, "false": bad,
                          "correct": kept + bad - added,
                          "mean_reward_error": round(sum(r["weight"] *
                              (r["judgments"][method] - r["met"]) for r in rows) / len(rows), 8)}
    return output


def replay(rows):
    assert partner.plan() == read(PARTNER / "plan.json")
    original = read(PARTNER / "results.json")
    table = team.tables()
    n = partner.previous.EPISODES
    rng = np.random.default_rng(partner.SEED)
    draws = (rng.integers(3, size=n), rng.random(n) < 0.5,
             rng.random(n) < partner.previous.DELIVERY, rng.random(n) < partner.previous.DELIVERY,
             (rng.random(n) < 0.5).astype(int))
    probes = rng.random((3, partner.PROBES))
    result = {}
    for mode in METHODS:
        modified = list(table)
        modified[3] = table[3].copy()
        for docket, (family, views) in enumerate(team.PRIVATE.items()):
            for i, name in enumerate(views):
                for j, choice in enumerate(team.ACTIONS):
                    row = rows[f"{family}/{name}/{choice}"]
                    modified[3][docket, i, j] += row["weight"] * (row["judgments"][mode] - row["met"])
        all_held = []
        for docket, family in enumerate(team.PRIVATE):
            exact_replay = partner.collect(table, docket, draws)
            assert exact_replay[-1] == original["dockets"][family]["exploration"]
            judged = partner.collect(modified, docket, draws)
            assert [r | {"score": 0} for r in judged[-1]] == [r | {"score": 0} for r in exact_replay[-1]]
            pooled = partner.fit(judged, True)
            conditioned = partner.fit(judged, False)
            legacy = np.zeros((3, 2))
            held = partner.evaluate(table, docket, (legacy, pooled, conditioned), probes)
            for row in held:
                row["family"] = family
                row["policies"] = {key: row["policies"][key] for key in ("reply_conditioned_declared", "oracle")}
            assert all(r["policies"]["oracle"]["utility"] == o["policies"]["oracle"]["utility"]
                       for r, o in zip(held, original["dockets"][family]["held"], strict=True))
            all_held.extend(held)
        result[mode] = {
            "judged_complete_score_table": modified[3].tolist(),
            "overall": partner.summarize(all_held),
            "by_family": {family: partner.summarize([r for r in all_held if r["family"] == family])
                          for family in team.PRIVATE},
        }
    return result


def run():
    rows = judged_rows()
    real = [row for row in rows.values() if not row["mutation"]]
    changed = [row for row in rows.values() if row["mutation"]]
    return {"judgments": rows, "archived_record_metrics": summarize(real),
            "mutation_metrics": summarize(changed), "downstream_replay": replay(rows)}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, ensure_ascii=False))
