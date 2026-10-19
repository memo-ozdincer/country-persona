"""Replay native48 masks/exposures, historical comparators and all inspected outputs."""
import argparse
from collections import Counter
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
from country_persona.io import sha256,write_json
from country_persona.scenario_sft import audit_trace,locked_runtime
from run_native_scope_partial import PACK,prepare,replay_comparators


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--output",type=Path,required=True);a=p.parse_args()
    assert not a.output.exists()
    cfg=json.loads((PACK/"config.json").read_text())
    from transformers import AutoTokenizer
    tok=AutoTokenizer.from_pretrained(cfg["model_path"],local_files_only=True)
    rows=prepare(tok);fitting=[r for r in rows if r["split"]=="train"]
    for path,expected in json.loads((PACK/"release.json").read_text())["files_sha256"].items():
        assert sha256(ROOT/path)==expected,path
    parent=json.loads((ROOT/"research/native-application-writer-20261019-v1/examples.json").read_text())
    for row in fitting:
        if row["id"]=="partial-9214-IND":continue
        old=next(r for r in parent if r["id"]==row["id"])
        assert all(row[k]==old[k] for k in ["messages","target","units"])
    new=next(r for r in fitting if r["id"]=="partial-9214-IND")
    old=next(r for r in parent if r["id"]=="application-9214-IND")
    assert new["messages"][1]["content"].split("\nEXPLICIT HYPOTHETICAL WORKPLAN Q\n")[0]==old["messages"][1]["content"].split("\nHYPOTHETICAL APPLICATION Q\n")[0]
    assert {r["episode"] for r in fitting}=={"8923","9214"}
    run=ROOT/"runs/native-scope-partial-writer-20261019-v1"
    launch=json.loads((run/"launch.json").read_text());assert launch["status"]=="completed"
    assert launch["runtime"]==locked_runtime() and launch["gpu"]["name"]=="NVIDIA RTX PRO 6000 Blackwell Server Edition"
    assert launch["production_optimizer_updates"]==48 and launch["completed_stages"]==cfg["evaluation_stages"]
    assert json.loads((run/"actual-inputs-and-masks.json").read_text())==rows
    historical=replay_comparators(tok,rows);assert historical==json.loads((run/"comparator-replay.json").read_text())
    training=json.loads((run/"training-result.json").read_text());trace=audit_trace(run/"optimization.jsonl",fitting,8,42)
    assert trace["entries"]==training["steps"]==48
    assert training["sequence_tokens"]==sum(len(r["input_ids"]) for r in fitting)*8
    assert training["supervised_tokens"]==sum(r["supervised_tokens"] for r in fitting)*8
    assert training["base_tensor_versions_unchanged"]
    assert training["serialization"]["same_base_probe_logits_equal"] and training["serialization"]["maximum_logit_difference"]==0
    for name,expected in training["serialization"]["files_sha256"].items():
        assert sha256(run/"adapter"/name)==expected
    # Separate cold CPU deserialization of saved tensors, without claiming fresh-base probe equality.
    from safetensors.torch import load_file
    from country_persona.training_checks import tensor_state_digest
    cold=tensor_state_digest(load_file(run/"adapter/adapter_model.safetensors",device="cpu"))
    assert cold==training["update"]["final_adapter_digest"]
    rubric_path=PACK/"rubric.json";rubric=json.loads(rubric_path.read_text());stages={};total=0
    for stage in cfg["evaluation_stages"]:
        selected={r["id"]:r for r in fitting if stage=="fitting"} if stage=="fitting" else {r["id"]:r for r in rows if r["split"]==stage}
        dest=run/stage;responses=[json.loads(s) for s in (dest/"responses.jsonl").read_text().splitlines()]
        review=json.loads((dest/"inspection.json").read_text());assert review["complete_outputs_read"] is True and review["independent_review_complete"] is False
        assert review["responses_sha256"]==sha256(dest/"responses.jsonl") and review["rubric_sha256"]==sha256(rubric_path)
        items={r["id"]:r for r in review["records"]};assert set(items)==set(selected)=={r["id"] for r in responses}
        assert len(items)==len(responses)
        material,guards,coverage=Counter(),Counter(),Counter();strict=contract=exact=tokens=0;details={}
        for response in responses:
            row=selected[response["id"]];item=items[row["id"]]
            assert response["prefix_ids"]==row["prefix_ids"] and response["prefix_sha256"]==row["prefix_sha256"]
            assert tok.decode(response["output_ids"],skip_special_tokens=False)==response["output_raw"]
            assert tok.decode(response["output_ids"],skip_special_tokens=True)==response["output_display"]
            assert len(response["output_ids"])==response["generated_tokens"] and not response["at_cap"]
            assert item["words"]==len(response["output_display"].split())
            assert set(item["material"])==set(rubric["units"][row["id"]]) and set(item["guards"])==set(rubric["guards"])
            extra=item.get("source_map",{});assert set(extra)==set(rubric["source_map_units"].get(row["id"],{}))
            ratings=list(item["material"].values())+list(item["guards"].values())+list(extra.values())
            assert all(r in {"met","unmet","uncertain"} for r in ratings)
            assert item["strict_pass"]==all(r=="met" for r in ratings)
            assert (item["guards"]["length"]=="met")== (item["words"]<=240)
            assert isinstance(item["requested_scope_followed"],bool)
            assert item["complete_output_contract_pass"]==(item["strict_pass"] and item["requested_scope_followed"])
            material.update(item["material"].values());guards.update(item["guards"].values());coverage.update(extra.values())
            strict+=item["strict_pass"];contract+=item["complete_output_contract_pass"]
            exact+=row["target"] is not None and response["output_display"].strip()==row["target"].strip()
            tokens+=response["generated_tokens"]
            details[row["id"]]=dict(words=item["words"],strict_pass=item["strict_pass"],scope_followed=item["requested_scope_followed"],complete_output_contract_pass=item["complete_output_contract_pass"])
        total+=len(responses)
        stages[stage]=dict(answers=len(responses),material=dict(material),guards=dict(guards),source_map=dict(coverage),
            strict_passes=strict,complete_output_contract_passes=contract,exact_targets=exact,generated_tokens=tokens,details=details)
    assert total==launch["production_generation_records"]==15
    write_json(a.output,dict(status="48_actual_updates_15_outputs_masks_scope_reviews_and_cold_saved_tensors_replayed",
        production_generation_records=15,historical_comparators_replayed_without_calls=sum(x["records"] for x in historical.values()),
        optimizer_updates=48,cumulative_qwen35_updates=4182,fit_sequence_tokens=training["sequence_tokens"],fit_supervised_tokens=training["supervised_tokens"],
        adapter_tensor_digest=cold,cold_saved_tensor_deserialization_exact=True,same_base_reload_probe_exact=True,
        stages=stages,independent_semantic_review_complete=False,scope="Software integrity and same-assistant arithmetic; no independent/persona/collective/sealedOOD claim."))
    print(json.dumps(json.loads(a.output.read_text()),indent=2))


if __name__=="__main__":main()
