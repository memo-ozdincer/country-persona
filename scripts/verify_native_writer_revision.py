"""Replay two exact common-draft revisions and same-assistant rating arithmetic."""
import argparse
from collections import Counter
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from country_persona.io import sha256, write_json
from country_persona.scenario_sft import ids_digest, locked_runtime


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args(); assert not args.output.exists()
    pack = ROOT / "research/native-writer-revision-20261019-v1"
    run = ROOT / "runs/native-writer-revision-20261019-v1"
    for path, expected in json.loads((pack / "release.json").read_text())["files_sha256"].items():
        assert sha256(ROOT / path) == expected
    cfg = json.loads((pack / "config.json").read_text())
    row = json.loads((pack / "example.json").read_text())
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(cfg["model_path"], local_files_only=True)
    ids = tok.apply_chat_template(row["messages"], tokenize=True, return_dict=False,
                                 add_generation_prompt=True, enable_thinking=False)
    actual = json.loads((run / "actual-input.json").read_text())
    assert actual == dict(**row, prefix_ids=ids, prefix_sha256=ids_digest(ids))
    protocol = json.loads((pack / "protocol.json").read_text())
    assert sha256(ROOT / protocol["common_seed_path"]) == protocol["common_seed_sha256"]
    draft = json.loads((ROOT / protocol["common_seed_path"]).read_text())["output_display"]
    parent = next(r for r in json.loads((ROOT / "research/native-application-writer-20261019-v1/examples.json").read_text()) if r["id"] == "application-9469-BRA")
    assert row["messages"][0] == parent["messages"][0]
    assert row["messages"][1]["content"].startswith(parent["messages"][1]["content"])
    assert "\nDRAFT\n" + draft + "\nEND OF DRAFT\n" in row["messages"][1]["content"]
    launch = json.loads((run / "launch.json").read_text())
    assert launch["status"] == "completed" and launch["production_optimizer_updates"] == 0
    assert launch["production_generation_records"] == 2 and launch["runtime"] == locked_runtime()
    assert launch["gpu"]["name"] == "NVIDIA RTX PRO 6000 Blackwell Server Edition"
    assert launch["adapter_digest"] == cfg["adapter_tensor_digest"]
    assert json.loads((run / "decoder.json").read_text()) == json.loads((ROOT / cfg["decoder_path"]).read_text())
    rubric = json.loads((pack / "rubric.json").read_text()); stages = {}
    parent_rubric = json.loads((ROOT / "research/native-application-writer-20261019-v1/rubric.json").read_text())
    assert rubric["units"][row["id"]] == parent_rubric["units"][parent["id"]]
    assert rubric["guards"] == parent_rubric["guards"]
    for arm in ["base", "adapter"]:
        dest = run / arm; response = json.loads((dest / "responses.jsonl").read_text())
        review = json.loads((dest / "inspection.json").read_text())
        assert review["complete_outputs_read"] is True and review["independent_review_complete"] is False
        assert review["responses_sha256"] == sha256(dest / "responses.jsonl")
        assert review["rubric_sha256"] == sha256(pack / "rubric.json")
        assert response["prefix_sha256"] == ids_digest(ids)
        assert tok.decode(response["output_ids"], skip_special_tokens=False) == response["output_raw"]
        assert tok.decode(response["output_ids"], skip_special_tokens=True) == response["output_display"]
        assert response["generated_tokens"] == len(response["output_ids"]) and not response["at_cap"]
        assert len(review["records"]) == 1
        item = review["records"][0]; assert item["id"] == row["id"] == response["id"]
        assert item["words"] == len(response["output_display"].split())
        assert set(item["material"]) == set(rubric["units"][row["id"]])
        assert set(item["guards"]) == set(rubric["guards"])
        ratings = list(item["material"].values()) + list(item["guards"].values())
        assert all(x in {"met", "unmet", "uncertain"} for x in ratings)
        assert item["strict_pass"] == all(x == "met" for x in ratings)
        assert (item["guards"]["length"] == "met") == (item["words"] <= 240)
        stages[arm] = dict(material=dict(Counter(item["material"].values())),
            guards=dict(Counter(item["guards"].values())), words=item["words"],
            strict_pass=item["strict_pass"], generated_tokens=response["generated_tokens"])
    write_json(args.output, dict(status="two_common_draft_native_revisions_replayed", generation_records=2,
        optimizer_updates=0, same_actual_input_both_arms=True, original_dossier_and_plan_unchanged=True,
        cold_adapter_tensor_state_exact=True, adapter_tensor_digest=launch["adapter_digest"],
        stages=stages, independent_semantic_review_complete=False,
        scope="Adaptive one-case revision diagnostic; no peer-effect or sealedOOD claim."))
    print(json.dumps(json.loads(args.output.read_text()), indent=2))


if __name__ == "__main__":
    main()
