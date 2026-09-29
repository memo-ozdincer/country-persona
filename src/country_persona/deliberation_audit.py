"""Replay transcript dependencies and report mechanical, not semantic, outcomes."""
from collections import Counter
from copy import deepcopy

from .deliberation import CONDITIONS, COUNTRIES, run_condition


def validate_transcript(scenarios, rows):
    if not rows or len({r["response_id"] for r in rows}) != len(rows):
        raise ValueError("Empty or duplicate transcript responses")
    position = 0

    def replay(case, cap, adapter_permitted):
        nonlocal position
        if position >= len(rows):
            raise ValueError("Transcript ends before the protocol completes")
        row = rows[position]
        position += 1
        if row["case"] != case:
            raise ValueError("Transcript prompt/history differs from the declared protocol")
        for key in ("id", "case_sha256", "scenario_id", "scenario_sha256", "country", "condition", "stage", "depends_on_response_ids"):
            if row.get(key) != case[key]:
                raise ValueError("Transcript metadata differs from the replayed case")
        if row.get("maximum_output_tokens") != cap or row.get("adapter_permitted") != adapter_permitted:
            raise ValueError("Changed output budget or aggregator policy")
        if row.get("adapter_active") and not adapter_permitted:
            raise ValueError("Final aggregator must remain the unadapted base model")
        for key in ("prompt_tokens", "generated_tokens"):
            if type(row[key]) is not int or row[key] < 1:
                raise ValueError("Invalid token accounting")
        return deepcopy(row)

    for scenario in scenarios:
        for condition in CONDITIONS:
            run_condition(scenario, condition, replay)
    if position != len(rows):
        raise ValueError("Transcript has extra responses outside the protocol")
    return {"responses": position, "exact_prompt_and_history_replay": True}


def mechanical_summary(scenarios, rows):
    replay = validate_transcript(scenarios, rows)
    index = {(r["scenario_id"], r["condition"], r["country"], r["stage"]): r for r in rows}
    initial_pairs, revisions, conditions = [], [], []
    for scenario in scenarios:
        for country in COUNTRIES:
            left = index[(scenario["id"], "independent_revision", country, "initial")]
            right = index[(scenario["id"], "peer_revision", country, "initial")]
            initial_pairs.append({"scenario_id": scenario["id"], "country": country,
                                  "identical_input_tokens": left["input_ids"] == right["input_ids"],
                                  "identical_generated_tokens": left["generated_ids"] == right["generated_ids"]})
        for condition in CONDITIONS:
            group = [r for r in rows if r["scenario_id"] == scenario["id"] and r["condition"] == condition]
            conditions.append({"scenario_id": scenario["id"], "condition": condition, "calls": len(group),
                               "prompt_tokens": sum(r["prompt_tokens"] for r in group),
                               "generated_tokens": sum(r["generated_tokens"] for r in group),
                               "generation_seconds": sum(r["generation_seconds"] for r in group),
                               "trace_processing_seconds": sum(r["trace_processing_seconds"] for r in group),
                               "output_caps": sum(r["hit_output_cap"] for r in group),
                               "maximum_prompt_tokens": max(r["prompt_tokens"] for r in group)})
    for row in rows:
        if row["stage"] not in {"revision", "central_revision"}:
            continue
        stage = "initial" if row["stage"] == "revision" else "central_initial"
        initial = index[(row["scenario_id"], row["condition"], row["country"], stage)]
        revisions.append({"scenario_id": row["scenario_id"], "condition": row["condition"], "country": row["country"],
                          "text_changed": row["output"] != initial["output"],
                          "initial_capped": initial["hit_output_cap"], "revision_capped": row["hit_output_cap"]})
    return {**replay, "conditions": conditions, "initial_control_pairs": initial_pairs, "revision_changes": revisions,
            "output_caps": sum(r["hit_output_cap"] for r in rows),
            "caps_by_stage": dict(Counter(r["stage"] for r in rows if r["hit_output_cap"])),
            "thinking_marker_outputs": sum(r["generated_thinking_marker"] for r in rows),
            "empty_outputs": sum(not r["output"].strip() for r in rows),
            "total_prompt_tokens": sum(r["prompt_tokens"] for r in rows),
            "total_generated_tokens": sum(r["generated_tokens"] for r in rows),
            "total_generation_seconds": sum(r["generation_seconds"] for r in rows),
            "total_trace_processing_seconds": sum(r["trace_processing_seconds"] for r in rows),
            "maximum_duplicate_8gram_fraction": max(r["repetition"]["duplicate_8gram_fraction"] for r in rows),
            "quality_scores": None,
            "limitations": ["Text changes, repeatability and agreement do not establish policy fidelity or deliberation benefit.",
                            "Capped answers remain in the denominator; do not silently remove them from quality review.",
                            "Trace processing is instrument overhead and is reported separately from model generation."]}
