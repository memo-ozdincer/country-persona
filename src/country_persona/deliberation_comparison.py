"""Paired checkpoint comparisons with explicit provenance and missing-rating rules."""
from pathlib import Path

from .deliberation_review import score_deliberation


def _key(row):
    return tuple(row[k] for k in ("scenario_id", "condition", "country", "stage"))


def compare_checkpoints(before_run, after_run, before_rows, after_rows, references, before_reviews=(), after_reviews=()):
    for record in (before_run, after_run):
        if record.get("status") != "completed" or record.get("snapshot_verification", {}).get("status") != "verified_current_bytes":
            raise ValueError("Both checkpoints require completed inference and verified base bytes")
    for key in ("model", "revision", "model_lock_sha256", "pack_manifest_sha256", "protocol_sha256", "chat_template_kwargs", "seed", "generation_call_kwargs", "torch_version", "transformers_version", "device"):
        if key not in before_run or key not in after_run or before_run[key] != after_run[key]:
            raise ValueError("Checkpoint comparison differs in " + key)
    code_before = {Path(k).name: v for k, v in before_run["source_code_sha256"].items()}
    code_after = {Path(k).name: v for k, v in after_run["source_code_sha256"].items()}
    if not code_before or not before_run["snapshot_verification"]["files"] or code_before != code_after or before_run["snapshot_verification"]["files"] != after_run["snapshot_verification"]["files"]:
        raise ValueError("Changed inference code or base checkpoint bytes")
    if before_run.get("adapter") is not None or not after_run.get("adapter"):
        raise ValueError("Expected an unadapted baseline and an explicitly recorded trained adapter")
    before_index, after_index = ({_key(r): r for r in rows} for rows in (before_rows, after_rows))
    if not before_index or len(before_index) != len(before_rows) or len(after_index) != len(after_rows) or set(before_index) != set(after_index):
        raise ValueError("Unmatched checkpoint response groups")
    for key, before in before_index.items():
        after = after_index[key]
        for name in ("scenario_sha256", "maximum_output_tokens", "generation_config"):
            if before[name] != after[name]:
                raise ValueError("Changed evidence, output budget or decoding settings")
        if before.get("adapter_active") is not False or after.get("adapter_active") != (after["stage"] != "synthesis"):
            raise ValueError("Wrong agent/aggregator adapter state")
    before_scores = score_deliberation(before_rows, references, before_reviews)
    after_scores = score_deliberation(after_rows, references, after_reviews)
    left = {_key(r): r for r in before_scores["scores"]}
    right = {_key(r): r for r in after_scores["scores"]}
    pairs = []
    for key in sorted(left):
        a, b = left[key], right[key]
        complete = a["all_ratings_complete"] and b["all_ratings_complete"]
        pairs.append({**dict(zip(("scenario_id", "condition", "country", "stage"), key)),
                      "before_response_id": a["response_id"], "after_response_id": b["response_id"],
                      "both_fully_rated": complete,
                      "content_met_rate_before": a["content_met_rate"], "content_met_rate_after": b["content_met_rate"],
                      "content_met_rate_delta": b["content_met_rate"] - a["content_met_rate"] if a["content_met_rate"] is not None and b["content_met_rate"] is not None else None,
                      "new_failed_checks": sorted(set(b["known_failed_checks"]) - set(a["known_failed_checks"])) if complete else None,
                      "resolved_failed_checks": sorted(set(a["known_failed_checks"]) - set(b["known_failed_checks"])) if complete else None})
    before_contrasts = {r["scenario_id"]: r for r in before_scores["paired_deliberation_contrasts"]}
    gains = []
    for after in after_scores["paired_deliberation_contrasts"]:
        before = before_contrasts[after["scenario_id"]]
        a, b = before["country_macro_peer_gain"], after["country_macro_peer_gain"]
        gains.append({"scenario_id": after["scenario_id"], "peer_gain_before_training": a, "peer_gain_after_training": b,
                      "training_change_in_peer_gain": b - a if a is not None and b is not None else None})
    cost = []
    for scenario, condition in sorted({(r["scenario_id"], r["condition"]) for r in before_rows}):
        entry = {"scenario_id": scenario, "condition": condition}
        for name, rows in (("before", before_rows), ("after", after_rows)):
            group = [r for r in rows if r["scenario_id"] == scenario and r["condition"] == condition]
            entry[name] = {"prompt_tokens": sum(r["prompt_tokens"] for r in group), "generated_tokens": sum(r["generated_tokens"] for r in group),
                           "generation_seconds": sum(r["generation_seconds"] for r in group), "output_caps": sum(r["hit_output_cap"] for r in group)}
        cost.append(entry)
    return {"status": "paired_arithmetic_not_a_semantic_judge", "matched_responses": len(pairs),
            "fully_rated_pairs": sum(p["both_fully_rated"] for p in pairs),
            "before_reviewer_kinds": before_scores["reviewer_kinds"], "after_reviewer_kinds": after_scores["reviewer_kinds"],
            "response_pairs": pairs, "deliberation_gain_change": gains, "actual_costs": cost,
            "limitations": ["Use independently calibrated ratings. An assistant or fixture score is not a human-validated research result.",
                            "The peer gain subtracts self-revision improvement at each checkpoint; training change subtracts those gains across checkpoints.",
                            "Countries within an event are dependent; this development comparison produces no significance test or population estimate.",
                            "Equal output allowances do not imply equal consumed compute; both costs and quality changes must be inspected."]}
