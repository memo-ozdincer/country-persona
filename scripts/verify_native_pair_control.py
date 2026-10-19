"""Replay a frozen one-case base/adapter control; not independent semantic review."""
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
    p.add_argument("--pack", type=Path, required=True)
    p.add_argument("--run", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args(); assert not a.output.exists()
    pack, run = a.pack.resolve(), a.run.resolve()
    for path, expected in json.loads((pack / "release.json").read_text())["files_sha256"].items():
        assert sha256(ROOT / path) == expected, path
    protocol = json.loads((pack / "protocol.json").read_text())
    for path, expected in protocol["unchanged_file_bindings"].items():
        assert sha256(ROOT / path) == expected, path
    cfg = json.loads((pack / "config.json").read_text())
    row = json.loads((pack / "example.json").read_text())
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(cfg["model_path"], local_files_only=True)
    ids = tok.apply_chat_template(row["messages"], tokenize=True, return_dict=False,
                                 add_generation_prompt=True, enable_thinking=False)
    assert json.loads((run / "actual-input.json").read_text()) == dict(**row, prefix_ids=ids, prefix_sha256=ids_digest(ids))
    launch = json.loads((run / "launch.json").read_text())
    assert launch["status"] == "completed" and launch["production_optimizer_updates"] == 0
    assert launch["production_generation_records"] == 2 and launch["runtime"] == locked_runtime()
    assert launch["gpu"]["name"] == "NVIDIA RTX PRO 6000 Blackwell Server Edition"
    assert launch["adapter_digest"] == cfg["adapter_tensor_digest"]
    assert launch["actual_input_sha256"] == sha256(run / "actual-input.json")
    assert launch["release_sha256"] == sha256(pack / "release.json")
    assert json.loads((run / "decoder.json").read_text()) == json.loads((ROOT / cfg["decoder_path"]).read_text())
    for name, expected in cfg["adapter_files_sha256"].items():
        assert sha256(ROOT / cfg["adapter_path"] / name) == expected
    rubric = json.loads((pack / "rubric.json").read_text()); stages = {}
    for arm in ["base", "adapter"]:
        dest = run / arm; response = json.loads((dest / "responses.jsonl").read_text())
        review = json.loads((dest / "inspection.json").read_text())
        assert review["complete_outputs_read"] is True and review["independent_review_complete"] is False
        assert review["responses_sha256"] == sha256(dest / "responses.jsonl")
        assert review["rubric_sha256"] == sha256(pack / "rubric.json")
        assert response["prefix_sha256"] == ids_digest(ids)
        assert response["arm"] == arm
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
    write_json(a.output, dict(status="two_actual_native_control_outputs_and_reviews_replayed", generation_records=2,
        optimizer_updates=0, cumulative_qwen35_updates=4134, same_actual_input_both_arms=True,
        cold_adapter_tensor_state_exact=True, adapter_tensor_digest=launch["adapter_digest"],
        stages=stages, independent_semantic_review_complete=False, scope=protocol["scope"]))
    print(json.dumps(json.loads(a.output.read_text()), indent=2))


if __name__ == "__main__":
    main()
