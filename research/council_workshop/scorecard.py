"""Rebuild the workshop scorecard from archived traces without model calls."""

from collections import Counter
import json
import subprocess
import sys

from held_suite import FAMILIES, audit, score
from replay import replay
from run import HERE, pretty


ROOT = HERE.parents[1]
REPORTS = ROOT / "reports"


def report(name):
    return REPORTS / f"council-workshop-{name}-20261123"


def verified_json(artifact, command, *args):
    expected = artifact.read_bytes()
    output = subprocess.check_output([sys.executable, "-B", str(command), *map(str, args)], cwd=ROOT)
    if output != expected:
        raise ValueError(f"Replayed output differs from {artifact.relative_to(ROOT)}")
    return json.loads(output)


def endpoint(row):
    speeches = row["speeches"]
    return {"outcome": row["outcome"], "reward": row["reward"],
            "speeches": len(speeches) if isinstance(speeches, list) else speeches,
            "calls": row["calls"], "signature_count": len(row["signatures"]),
            "exclusion_count": len(row["exclusions"])}


def caps(settings):
    return {"turn_cap": settings["turn_cap"], "call_cap": settings.get("call_cap")}


def registered_paths():
    held = report("held-pilot")
    paths = [held / name for name in (
        "all-sol", "feasible-all-sol", "sol-with-astra-norway", "feasible-sol-with-astra-norway",
    )]
    paths.extend(report("iraq-pilot") / name for name in ("all-sol", "sol-with-astra-uae-resumed"))
    paths.append(report("exclusion-policy") / "iraq-feasible-standard")
    paths.extend(report("norway-opening") / name for name in ("all-sol", "sol-with-astra-norway-resumed"))
    paths.extend(report("all-sol-matrix") / name for name in (
        "guinea-norway-feasible", "iraq-uae-impasse", "iraq-uae-feasible",
    ))
    return paths


def build():
    clauses = {}
    for name in ("astra", "sol"):
        directory = report("20") / name
        source = report("clause-review")
        review = verified_json(source / f"{name}-score.json", HERE / "review.py", directory,
                               "--verdict", source / f"{name}-verdict.json")
        result = replay(directory)
        settings = json.loads((directory / "settings.json").read_text())
        clauses[settings["model"]] = {**caps(settings), "outcome": result["status"], "speeches": len(result["history"]),
                                      "coverage": review["semantic_points"], "review": "retrospective_assistant"}

    blind = report("blind-judge")
    judgments = verified_json(blind / "score.json", blind / "blind-review.py", "score")
    for model, record in (("gpt-6.2-sol", "record-01"), ("gpt-6.2-astra", "record-02")):
        row = judgments[record]
        clauses[model]["blinded_model_regrade"] = {
            "coverage": row["model_review"]["semantic_points"], "matching_criteria": row["criterion_agreement"],
            "guard": row["model_review"]["guard"],
        }
    anchor = judgments["guard-control"]

    climate = report("sol-control")
    pair = verified_json(climate / "comparison.json", climate / "compare.py")
    climate_caps = {case: caps(json.loads((climate / directory / "settings.json").read_text()))
                    for case, directory in (("feasible", "feasible"), ("impasse", "impasse"),
                                            ("feasible_continuations", "feasible-extended"))}
    registered = score(registered_paths())
    registered["caps_by_family"] = {name: caps(family) for name, family in FAMILIES.items()}
    scripted = audit()
    if scripted != json.loads((HERE / "held-control-audit.json").read_text()):
        raise ValueError("The scripted reachability audit differs from its archive")
    all_sol = [row for row in registered["meetings"] if row["arm"] == "all-sol"]
    all_sol_summary = {"planned": len(scripted), "scored": sum(row["reward"] is not None for row in all_sol),
                       "outcomes_by_world": {
                           world: dict(sorted(Counter(r["outcome"] for r in all_sol if r["world"] == world).items()))
                           for world in ("feasible", "impasse")
                       }}
    matrix = report("all-sol-matrix")
    extra_call = verified_json(matrix / "continuation.json", matrix / "verify-continuation.py")
    moderator = report("moderator-certificate")
    stops = verified_json(moderator / "results.json", moderator / "replay-stop.py")
    headroom = report("budget-headroom")
    budget = verified_json(headroom / "results.json", headroom / "audit.py")

    experiments = (("iraq", "exclusion-policy", "readout"), ("gulf", "exclusion-transfer", "transfer"),
                   ("conditional", "conditional-exclusions", "readout"),
                   ("feasible_opening", "opening-agreement", "readout"),
                   ("rejected_opening", "rejected-opening", "readout"))
    prompts = {}
    for name, directory, stem in experiments:
        source = report(directory)
        rows = verified_json(source / f"{stem}.json", source / f"{stem}.py")
        if name in ("feasible_opening", "rejected_opening"):
            rows = {"live": rows["live"], "scripted": rows["scripted"]}
        prompts[name] = {world: {arm: endpoint(row) for arm, row in arms.items()} for world, arms in rows.items()}

    fork = report("rejection-fork")
    design = verified_json(fork / "fork.json", fork / "fork.py", "build")
    choices = verified_json(fork / "score.json", fork / "fork.py", "score")
    expanded = verified_json(fork / "budget-relaxation.json", fork / "budget-relaxation.py")
    live = report("live-rejection-fork")
    rollouts = {}
    for world in ("feasible", "impasse", "impasse-checked-rejection"):
        row = verified_json(live / f"{world}-result.json", live / "rollout.py", "replay", world)
        rollouts[world] = endpoint(row) | {"decision_counts": row["decision_counts"]}

    return {
        "source_clause_case": clauses,
        "source_clause_guard_control": {
            "reviewer": "gpt-6.1-sol", "caught_authored_false_claim": anchor["caught_authored_false_claim"],
            "coverage": anchor["model_review"]["semantic_points"], "released_points": anchor["model_review"]["released_points"],
        },
        "five_seat_climate": {case: {"caps": climate_caps[case], "arms": {arm: endpoint(row) for arm, row in arms.items()}}
                              for case, arms in pair.items()},
        "registered_standard_prompt_cells": registered,
        "registered_all_sol_summary": all_sol_summary,
        "registered_all_sol_impasse_continuation": {
            "original": endpoint(extra_call["original"]), "continuation": endpoint(extra_call["continuation"]),
            "reused_calls": extra_call["reused_calls"], "extra_call": extra_call["extra_call"],
        },
        "moderator_certificate_replay": {
            "meetings": len(stops["meetings"]), "new_successes": stops["new_successes"],
            "total_calls_saved": stops["total_calls_saved"],
            "certificates_by_moderator": sum(row["automatic_certificate"] for row in stops["meetings"]),
        },
        "first_proven_all_sol_budget_failures": [
            {"family": row["family"], "order": row["order"], **row["first_proven_budget_failure"]}
            for row in budget["meetings"] if row["first_proven_budget_failure"] is not None
        ],
        "scripted_case_and_order_controls": {"successful": sum(r["reward"] for r in scripted), "total": len(scripted)},
        "matched_prompt_comparisons": prompts,
        "shared_observation_fork": {
            "frozen_next_speech": design["speech"], "original_speech_cap": design["turn_cap"],
            "call_cap": design["call_cap"],
            "original_exact_ceiling": design["uniform_world_success_ceiling"], "single_model_choices": choices,
            "relaxed_speech_cap": expanded["speech_cap"], "shared_scripted_policy_success": expanded["shared_policy_success"],
            "controlled_live_continuations": rollouts,
        },
    }


if __name__ == "__main__":
    print(pretty(build()))
