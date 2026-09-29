"""Join a frozen counterbalanced run and report all variants without selection."""
from collections import defaultdict
from datetime import datetime, timezone
import argparse
import json
from pathlib import Path

from country_persona.action_eval import index_unique, score_actions, validate_case
from country_persona.choice_stability import distribution_summary, summarize_group, summarize_groups
from country_persona.io import read_jsonl, sha256, write_json


def score(pack, run, baseline):
    manifest = json.loads((pack / "manifest.json").read_text())
    receipt = json.loads((run / "run.json").read_text())
    for name, expected in manifest["files_sha256"].items():
        if sha256(pack / name) != expected:
            raise ValueError("Pack hash mismatch")
    if receipt["status"] != "completed" or receipt["completed_cases"] != 200:
        raise ValueError("Expected all 200 completed outputs")
    if receipt["predictions_sha256"] != sha256(run / "predictions.jsonl"):
        raise ValueError("Prediction hash mismatch")
    if receipt["preflight"]["pack_manifest_sha256"] != sha256(pack / "manifest.json"):
        raise ValueError("Run used a different pack")
    cases = index_unique(list(read_jsonl(pack / "cases.jsonl")), "case")
    refs = index_unique(list(read_jsonl(pack / "action.references.jsonl")), "reference")
    preds = index_unique(list(read_jsonl(run / "predictions.jsonl")), "prediction")
    old = index_unique(list(read_jsonl(baseline / "predictions.jsonl")), "baseline")
    if set(cases) != set(refs) or set(cases) != set(preds):
        raise ValueError("Incomplete or extra IDs")
    # Reuse the strict action join for every row, including controls, but never
    # report this mixed denominator as historical benchmark performance.
    score_actions(list(cases.values()), list(refs.values()), list(preds.values()))
    buckets, replay = defaultdict(list), []
    for item in manifest["design"]:
        case = cases[item["id"]]
        validate_case(case)
        if item["kind"] == "baseline_replay":
            prior, now = old[case["id"]], preds[case["id"]]
            replay.append({"id": case["id"], "case_hash_equal": prior["case_sha256"] == now["case_sha256"],
                           "input_tokens_equal": prior["input_ids"] == now["input_ids"],
                           "output_tokens_equal": prior["generated_ids"] == now["generated_ids"],
                           "probabilities_equal": prior["probabilities"] == now["probabilities"]})
        else:
            buckets[item["kind"], case["parent_id"], case["country_form"]].append(case)
    groups = []
    for (kind, _, _), group in buckets.items():
        truths = {refs[c["id"]]["expected"] for c in group}
        if len(truths) != 1:
            raise ValueError("Conflicting references within a permutation group")
        groups.append({"kind": kind, **summarize_group(group, preds, truths.pop())})
    historical = [g for g in groups if g["kind"] == "historical_counterbalance"]
    controls = [g for g in groups if g["kind"] == "synthetic_extraction_control"]
    strata = {f"{arm}_{form}": summarize_groups([g for g in historical if g["condition"] == arm and g["country_form"] == form])
              for arm in ("A", "B") for form in ("iso", "name")}
    aliases = []
    for parent in sorted({g["parent_id"] for g in historical}):
        forms = {g["country_form"]: g for g in historical if g["parent_id"] == parent}
        a, b = forms["iso"], forms["name"]
        aliases.append({"parent_id": parent, "country": a["country"], "condition": a["condition"],
                        "expected": a["expected"], "iso_vote": a["mixture_vote"], "name_vote": b["mixture_vote"],
                        "agreement": a["mixture_vote"] is not None and a["mixture_vote"] == b["mixture_vote"],
                        "jsd_nats": distribution_summary([a["mean_probabilities"], b["mean_probabilities"]])["generalized_jsd_nats"]})
    numeric_rows = [preds[c["id"]] for c in cases.values() if "choice_labels" in c]
    return {"created_at": datetime.now(timezone.utc).isoformat(), "status": "development_diagnostic_completed",
            "protocol_sha256": manifest["protocol_sha256"], "pack_manifest_sha256": sha256(pack / "manifest.json"),
            "run_sha256": sha256(run / "run.json"), "predictions_sha256": sha256(run / "predictions.jsonl"),
            "source_sha256": {p: sha256(p) for p in [__file__, "src/country_persona/choice_stability.py", "src/country_persona/action_eval.py"]},
            "counts": manifest["counts"], "historical_strata": strata, "groups": groups, "country_alias_comparisons": aliases,
            "controls": summarize_groups(controls), "replays": replay,
            "all_original_replays_identical": all(all(r[k] for k in ("case_hash_equal", "input_tokens_equal", "output_tokens_equal", "probabilities_equal")) for r in replay),
            "diagnostics": {"output_caps": sum(p["hit_output_cap"] for p in preds.values()),
                            "thinking_markers": sum(p["generated_thinking_marker"] for p in preds.values()),
                            "digit_format_errors": sum(p["parsed_vote"] is None for p in numeric_rows),
                            "minimum_digit_legal_mass": min(p["legal_label_mass"] for p in numeric_rows)},
            "limits": manifest["limits"]}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pack", type=Path, required=True)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--baseline", type=Path, default=Path("runs/two-event-996664-base-v1"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("Choose a fresh report path")
    result = score(args.pack, args.run, args.baseline)
    write_json(args.output, result)
    print(json.dumps({k: result[k] for k in ("all_original_replays_identical", "diagnostics", "historical_strata")}, indent=2))
