"""Reproduce the declared eight-output diagnostic subset without editing its parent."""
import argparse
import json
from pathlib import Path

from country_persona.io import read_jsonl, sha256, write_json, write_jsonl


def select(pack, output, lock):
    if output.exists():
        raise ValueError("Choose a fresh probe directory")
    manifest = json.loads((pack / "manifest.json").read_text())
    for name in ("cases.jsonl", "action.references.jsonl", "policy.references.jsonl"):
        if sha256(pack / name) != manifest["files_sha256"][name]:
            raise ValueError("Parent evaluation pack changed")
    selected = [c for c in read_jsonl(pack / "cases.jsonl") if
                (c["task"] == "recorded_vote_prediction" and
                 ((c["country"] == "IND" and c["family"] == "unsc-climate-security-2021") or
                  (c["country"] in ("BRA", "FRA") and c["family"] == "unsc-ukraine-annexation-2022"))) or
                (c["task"] == "policy_fidelity" and c["country"] == "IND" and c["family"] == "unsc-climate-security-2021")]
    if len(selected) != 8 or len({r["pair_id"] for r in selected}) != 4:
        raise ValueError("Expected exactly the four declared A/B pairs")
    ids = {c["id"] for c in selected}
    output.mkdir(parents=True)
    write_jsonl(output / "cases.jsonl", selected)
    for name in ("action.references.jsonl", "policy.references.jsonl"):
        write_jsonl(output / name, (r for r in read_jsonl(pack / name) if r["id"] in ids))
    receipt = {"status": "inference_not_run", "parent_pack_manifest_sha256": sha256(pack / "manifest.json"),
               "selection": "Three action pairs spanning Y/N/A (FRA Ukraine, IND climate, BRA Ukraine), and the IND climate qualification policy pair. Diagnostic selection, not prevalence estimation.",
               "case_count": 8, "pair_count": 4, "event_count": 2, "planned_model_lock_sha256": sha256(lock),
               "planned_generation": {"do_sample": False, "max_new_tokens": 384, "total_context_budget": 8192,
                                      "eos_policy": "model generation_config defaults; record all effective EOS IDs and compare a bounded legacy single-EOS replay separately"},
               "required_trace_fields": ["full prompt token IDs or pinned reproducible input hash and count",
                                         "raw generated token IDs", "decoded text with and without special tokens",
                                         "stop reason and effective EOS IDs", "max output cap", "repeated token/phrase diagnostics",
                                         "seconds and input/output counts",
                                         "next-token Y/N/A probabilities conditional on legal labels plus total legal-label mass, for action tasks only"],
               "compute_status": "Trillium authentication required; no job submitted",
               "files_sha256": {name: sha256(output / name) for name in
                                ("policy.references.jsonl", "cases.jsonl", "action.references.jsonl")}}
    write_json(output / "manifest.json", receipt)
    return receipt


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pack", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--lock", type=Path, default=Path("configs/posttraining/model.lock.json"))
    args = parser.parse_args()
    result = select(args.pack, args.output, args.lock)
    print(f"Prepared {result['case_count']} cases; no inference performed.")
