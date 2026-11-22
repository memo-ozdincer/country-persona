"""Check whether any extra read helps under either frozen reviewer."""
from pathlib import Path
from statistics import mean

import numpy as np

import staged_route as staged

prior, HERE, team = staged.prior, staged.HERE, staged.team


def frontier(row, reviewer):
    possible = [[prior.stats(row, action, reply)[0] for reply in range(3)]
                for action in (2, 3)]
    greedy = staged.receiver(row, reviewer).argmax(axis=1).tolist()
    branch = [read[pick] for read, pick in zip(possible, greedy, strict=True)]
    first = prior.stats(row, 1, 0)[0]
    return {"first_only": first, "greedy_review_branches": branch, "best_legal_reply_by_branch": [
        max(v for v, legal in zip(per_read, mask, strict=True) if legal)
        for per_read, mask in zip(possible, row["legal"], strict=True)]}


def run():
    locked = team.read(HERE / "staged-results.json")
    original = team.read(HERE / "route-results.json")
    material = {}
    for source in prior.load():
        family, case = source["family"], source["key"]
        fitted, joint = (data["myanmar"] if family == "myanmar" else data["folds"][family]
                         for data in (locked, original))
        values = {name: frontier(source, np.asarray(result["weights"][1]))
                  for name, result in (("staged", fitted), ("joint", joint))}
        old = fitted["outcomes"][case]["policies"]
        assert old["first_only"]["net"] == values["staged"]["first_only"] == values["joint"]["first_only"]
        assert all(choices["relation"] == old["first_only"]["relation"]
                   for name, choices in old.items() if name in ("staged", "joint"))
        material[case] = {"family": family, **values}
    reports = {}
    archive = {row["family"] for row in material.values()} - {"myanmar"}
    for cohort, families in (("archive", archive), ("myanmar", {"myanmar"})):
        stats = {}
        for variant in ("staged", "joint"):
            cells = [r[variant] for r in material.values() if r["family"] in families]
            grouped = [[r[variant] for r in material.values() if r["family"] == f]
                       for f in sorted(families)]
            metrics = {"with_greedy_reviewer": "greedy_review_branches",
                       "with_hindsight_reply": "best_legal_reply_by_branch"}
            stats[variant] = {name: {
                "cases_beating_first": sum(max(r[field]) > r["first_only"] for r in cells),
                "cases_beating_best_no_query": sum(max(r[field]) > max(0., r["first_only"]) for r in cells),
                "cases": len(cells),
                "net_upper_bound": mean(mean(max(0.,r["first_only"],*r[field]) for r in family)
                                        for family in grouped)
            } for name, field in metrics.items()}
        reports[cohort] = stats
    paths = (Path(__file__), HERE / "route-results.json", HERE / "staged-results.json")
    return {"cases":material, "summary":reports, "sha256":{p.name:team.pin(p) for p in paths}}


if __name__ == "__main__":
    prior.study.e.emit(run())
