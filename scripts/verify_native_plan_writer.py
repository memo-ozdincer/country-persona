"""Replay native writer inputs/masks, 32 optimizer steps and actual generations.

Semantic ratings remain same-assistant judgments; this is a provenance and
arithmetic check, including explicit reused-baseline accounting.
"""
import argparse
from collections import Counter
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
from country_persona.io import sha256,write_json,digest
from country_persona.scenario_sft import ids_digest,audit_trace,locked_runtime
from run_native_plan_writer import prepare,PACK


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--output",type=Path,required=True);a=p.parse_args()
    assert not a.output.exists()
    cfg=json.loads((PACK/"config.json").read_text())
    from transformers import AutoTokenizer
    tok=AutoTokenizer.from_pretrained(cfg["model_path"],local_files_only=True)
    rows=prepare(tok);byid={r["id"]:r for r in rows};fitting=[r for r in rows if r["split"]=="train"]
    release=json.loads((PACK/"release.json").read_text())
    for path,expected in release["files_sha256"].items():assert sha256(ROOT/path)==expected,path
    grounding=json.loads((PACK/"grounding.json").read_text())
    prior=ROOT/"research/scenario-role-sft-20261017-v1"
    for case in grounding["grounding"]:
        body=grounding["statements"][case["id"]]
        assert __import__('hashlib').sha256(body.encode()).hexdigest()==case["body_sha256"]
        for point in case["points"]:
            for span in point["support"]:assert body[span["start"]:span["end"]]==span["quote"]
    source_rows=[json.loads(s) for s in (ROOT/grounding["source_rows_path"]).read_text().splitlines()]
    for r in source_rows:
        text=(prior/"sources"/("record-"+r["source"]+".txt")).read_text();start,end=r["provenance"]["target"]
        assert text[start:end]==r["body"]==grounding["statements"][r["id"]]
    wps=json.loads((ROOT/grounding["wps_path"]).read_text())
    text=(ROOT/"data/raw/source-application-grounding-20261003-v1/record-8514.txt").read_text()
    for country,r in wps.items():
        assert text[r["start"]:r["end"]].rstrip()==r["text"]==grounding["statements"]["8514-"+country]
        assert digest(r["text"])==r["text_digest"]
    vote=grounding["recorded_vote"]
    assert (ROOT/vote["path"]).read_text()[vote["start"]:vote["end"]]==vote["quote"]
    original=ROOT/"runs/native-plan-writer-20261019-v1"
    run=ROOT/"runs/native-plan-writer-resume-20261019-v1"
    old=json.loads((original/"launch.json").read_text());actual=json.loads((run/"launch.json").read_text())
    assert old["status"]=="failed" and old["production_optimizer_updates"]==0 and old["production_generation_records"]==2
    assert actual["status"]=="completed" and actual["production_optimizer_updates"]==32
    assert actual["runtime"]==locked_runtime() and old["runtime"]==actual["runtime"]
    assert actual["gpu"]["name"]==old["gpu"]["name"]=="NVIDIA RTX PRO 6000 Blackwell Server Edition"
    for row,stored in zip(rows,json.loads((run/"actual-inputs-and-masks.json").read_text())):assert row==stored
    assert sha256(run/"actual-inputs-and-masks.json")==sha256(original/"actual-inputs-and-masks.json")
    assert sha256(run/"base-source/responses.jsonl")==sha256(original/"base-source/responses.jsonl")
    assert json.loads((run/"decoder.json").read_text())==json.loads((original/"decoder.json").read_text())
    overlay=json.loads((PACK/"resume-lock.json").read_text())
    assert sha256(ROOT/"scripts/run_native_plan_writer_resume.py")==overlay["resume_runner_sha256"]
    for name,expected in overlay["base_files_sha256"].items():assert sha256(original/name)==expected
    training=json.loads((run/"training-result.json").read_text())
    trace=audit_trace(run/"optimization.jsonl",fitting,8,42)
    assert trace["entries"]==32 and training["base_tensor_versions_unchanged"]
    assert training["supervised_tokens"]==sum(r["supervised_tokens"] for r in fitting)*8==5856
    assert training["sequence_tokens"]==sum(len(r["input_ids"]) for r in fitting)*8==80992
    assert training["serialization"]["same_base_probe_logits_equal"] and training["serialization"]["maximum_logit_difference"]==0
    for name,expected in training["serialization"]["files_sha256"].items():assert sha256(run/"adapter"/name)==expected
    total=0;stages={}

    def check_record(record,messages):
        ids=tok.apply_chat_template(messages,tokenize=True,return_dict=False,add_generation_prompt=True,enable_thinking=False)
        assert record["prefix_sha256"]==ids_digest(ids)
        if "prefix_ids" in record:assert record["prefix_ids"]==ids
        assert tok.decode(record["output_ids"],skip_special_tokens=False)==record["output_raw"]
        assert tok.decode(record["output_ids"],skip_special_tokens=True)==record["output_display"]
        assert record["generated_tokens"]==len(record["output_ids"]) and not record["at_cap"]
        return len(record["output_ids"])

    def stage(path,rubric_path,expected_rows,addendum=None):
        nonlocal total
        responses=[json.loads(s) for s in (path/"responses.jsonl").read_text().splitlines()]
        assert {r["id"] for r in responses}==set(expected_rows)
        rubric=json.loads(rubric_path.read_text());review=json.loads((path/"inspection.json").read_text())
        assert review["responses_sha256"]==sha256(path/"responses.jsonl")
        assert review["rubric_sha256"]==sha256(rubric_path) and review["complete_outputs_read"] is True
        assert review["independent_review_complete"] is False
        counts,guards,coverage=Counter(),Counter(),Counter();passes=0;tokens=0
        for r in responses:
            tokens+=check_record(r,expected_rows[r["id"]]["messages"])
            item=review["answers"][r["id"]]
            assert set(item["units"])==set(rubric["units"][r["id"]])
            assert set(item["guards"])==set(rubric["guards"])
            assert item["words"]==len(r["output_display"].split())
            ratings=[v["rating"] for k in ["units","guards"] for v in item[k].values()]
            if addendum:
                assert review["coverage_addendum_sha256"]==sha256(addendum)
                extra=json.loads(addendum.read_text())["source_units"][r["id"]]
                assert set(item["source_map_units"])==set(extra)
                ratings += [v["rating"] for v in item["source_map_units"].values()]
                coverage.update(v["rating"] for v in item["source_map_units"].values())
            assert all(v in {"met","unmet","uncertain"} for v in ratings)
            strict=all(v=="met" for v in ratings);assert strict==item["strict_pass"]
            counts.update(v["rating"] for v in item["units"].values());guards.update(v["rating"] for v in item["guards"].values());passes+=strict
        total+=len(responses)
        return dict(answers=len(responses),material=dict(counts),guards=dict(guards),source_map=dict(coverage),strict_passes=passes,generated_tokens=tokens,responses_sha256=sha256(path/"responses.jsonl"))

    for name,split in [("base-source","eval"),("base-application","application_eval"),("adapter-fitting","train"),("adapter-source","eval")]:
        stages[name]=stage(run/name,PACK/"rubric.json",{r["id"]:r for r in rows if r["split"]==split})
    assert total==10 and actual["production_generation_records"]==8 and actual["reused_base_generation_records"]==2
    control=ROOT/"research/native-plan-writer-application-20261019-v1"
    frozen=json.loads((control/"release.json").read_text())
    for name,expected in frozen["files_sha256"].items():assert sha256(ROOT/name)==expected
    entry=json.loads((control/"execution-lock.json").read_text())
    assert sha256(ROOT/"scripts/run_native_plan_writer_application_control_v2.py")==entry["entrypoint_sha256"]
    assert sha256(control/"coverage-addendum.json")==entry["coverage_addendum_sha256"]
    live=json.loads((control/"runtime/launch.json").read_text());assert live["status"]=="completed"
    assert live["production_generated_answers"]==4 and live["production_optimizer_updates"]==0
    assert live["saved_adapter_digest"]==training["update"]["final_adapter_digest"]
    assert live["runtime"]==actual["runtime"] and live["gpu"]["name"]==actual["gpu"]["name"]
    cases={r["id"]:r for r in json.loads((control/"examples.json").read_text())}
    for arm in ["base","adapter"]:
        stages["corrected-application-"+arm]=stage(control/"runtime"/arm,control/"rubric.json",cases,control/"coverage-addendum.json")
    assert total==14
    report=dict(status="actual_native_tokens_masks_sources_32_steps_and_review_arithmetic_replayed",
        generated_records=14,reused_baseline_records_not_double_counted=2,production_optimizer_updates=32,
        cumulative_qwen35_updates=4094,fit_sequence_tokens=80992,fit_supervised_tokens=5856,complete_speech_source_spans_replayed=6,stages=stages,
        saved_adapter_digest=training["update"]["final_adapter_digest"],cold_adapter_tensor_state_exact=True,
        independent_semantic_review_complete=False,scope="Software/provenance replay; semantic ratings remain same-assistant development judgments.")
    write_json(a.output,report);print(json.dumps(report,indent=2))


if __name__=="__main__":main()
