"""Post-hoc diagnostic for a single tied order with a second formulation."""
from collections import Counter
import json

from scope_questions import HERE, clause_control, exclude, load, runner


def evaluate():
    sources = (
        HERE / "evidence/scope-questions/metrics.json",
        HERE / "evidence/scope-sets/metrics.json",
    )
    timing, complete_sets = map(load, sources)
    results, counts, routes, rescues = {}, Counter(), {}, []
    for panel in ("original", "reworded"):
        admitted = {}
        for card in ("japan", "china-overlap", "china-impasse"):
            key = f"{panel}/{card}"
            evidence = timing["questions"][key]
            status = {name: row["value"] for name, row in evidence.items()}
            margins = evidence["require_first"]["margins"]
            complete = complete_sets["projections"][key]["winner"]
            if min(margins) == 0 < max(margins) and complete == "broad-only" and status["forbid_first"] is False:
                status["require_first"] = True
                rescues.append(key)
            rejected, consistent = exclude(status)
            admitted[card] = rejected
            results[key] = {"rejected_scopes": sorted(rejected), "consistent": consistent}
        for episode, details in clause_control.evaluate(admitted)["paths"].items():
            prefix = panel + "/" + episode
            routes[prefix] = details
            counts[panel, episode.split("/")[0], details["public"]["state"]] += 1
    return {"scope": "Post-hoc, after observing a bfloat16 tie on one decision. Same two wordings of one case family. No new calls.",
            "inputs": {p.parent.name: runner.digest(p) for p in sources}, "rescued_ties": rescues,
            "totals": {"/".join(k): v for k, v in counts.items()}, "projections": results, "paths": routes}


if __name__ == "__main__":
    print(json.dumps(evaluate(), indent=2))
