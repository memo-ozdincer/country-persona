"""One fresh six-target fit; every evaluation group requires an inspected command."""
import argparse
import json
import os
from pathlib import Path
import select
import shutil
import subprocess
import sys
import time
import traceback

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
from country_persona.io import sha256,write_json
from country_persona.scenario_sft import ids_digest,locked_runtime,train_loop
from run_aurora_qwen35_smoke import current_gpu,identity,verify_model
from run_scenario_sft import fresh_adapter

PACK=ROOT/"research/native-scope-partial-writer-20261019-v1"


def prepare(tok):
    cfg=json.loads((PACK/"config.json").read_text());rows=json.loads((PACK/"examples.json").read_text())
    assert len(rows)==15 and {r["id"]:r["country"] for r in rows}==cfg["case_countries"]
    for r in rows:
        assert r["messages"][-1]["content"].endswith(r["country"]+" national delegation.")
        assert all("<|im_end|>" not in m["content"] and "<|im_start|>" not in m["content"] for m in r["messages"])
        prefix=tok.apply_chat_template(r["messages"],tokenize=True,return_dict=False,add_generation_prompt=True,enable_thinking=False)
        assert len(prefix)+2048<=8192 and prefix.count(tok.convert_tokens_to_ids("<|im_end|>"))==2
        r.update(prefix_ids=prefix,prefix_sha256=ids_digest(prefix))
        if r["target"] is not None:
            assert r["split"]=="train" and len(r["target"].split())<=240
            tail=tok.encode(r["target"]+"<|im_end|>",add_special_tokens=False)
            whole=tok.encode(tok.decode(prefix,skip_special_tokens=False)+r["target"]+"<|im_end|>",add_special_tokens=False)
            assert whole==prefix+tail
            r.update(input_ids=whole,labels=[-100]*len(prefix)+tail,prefix_tokens=len(prefix),supervised_tokens=len(tail))
        else:
            assert r["split"]!="train"
    fitting=[r for r in rows if r["split"]=="train"]
    assert len(fitting)==6 and {r["id"] for r in fitting}==set(cfg["fitting_ids"])
    assert cfg["updates"]==cfg["presentations"]*len(fitting)==48
    assert {r["episode"] for r in fitting}=={"9214","8923"}
    return rows


def replay_comparators(tok,rows):
    byid={r["id"]:r for r in rows};result={}
    protocol=json.loads((PACK/"protocol.json").read_text())
    for path,expected in protocol["unchanged_file_bindings"].items():
        assert sha256(ROOT/path)==expected,path
    for spec in json.loads((PACK/"comparators.json").read_text()):
        records=[json.loads(s) for s in (ROOT/spec["responses"]).read_text().splitlines()]
        actual=json.loads((ROOT/spec["actual_inputs"]).read_text())
        actual={r["id"]:r for r in actual} if isinstance(actual,list) else {actual["id"]:actual}
        review=json.loads((ROOT/spec["inspection"]).read_text())
        assert review["complete_outputs_read"] is True
        assert review["responses_sha256"]==sha256(ROOT/spec["responses"])
        for record in records:
            row=byid[record["id"]]
            assert actual[record["id"]]["messages"]==row["messages"]
            assert record["prefix_sha256"]==row["prefix_sha256"]
            assert tok.decode(record["output_ids"],skip_special_tokens=False)==record["output_raw"]
            assert tok.decode(record["output_ids"],skip_special_tokens=True)==record["output_display"]
        launch=json.loads((ROOT/spec["launch"]).read_text())
        assert launch["runtime"]==locked_runtime() and launch["gpu"]["name"]=="NVIDIA RTX PRO 6000 Blackwell Server Edition"
        result[spec["name"]]=dict(records=len(records),responses_sha256=sha256(ROOT/spec["responses"]),
            inspection_sha256=sha256(ROOT/spec["inspection"]),actual_prefixes_and_tokens_replayed=True,new_calls=0)
    assert sum(r["records"] for r in result.values())==18
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--output",type=Path,required=True)
    p.add_argument("--gpu-uuid");p.add_argument("--preflight-only",action="store_true");a=p.parse_args()
    out=a.output.resolve();out.mkdir(exist_ok=False)
    launch=dict(status="started",identity=identity(),runtime=locked_runtime(),output=str(out),code_sha256=sha256(Path(__file__)),
        production_generation_records=0,production_optimizer_updates=0)
    write_json(out/"launch.json",launch)
    try:
        for path,expected in json.loads((PACK/"release.json").read_text())["files_sha256"].items():
            assert sha256(ROOT/path)==expected,path
        cfg=json.loads((PACK/"config.json").read_text())
        from transformers import AutoTokenizer
        tok=AutoTokenizer.from_pretrained(cfg["model_path"],local_files_only=True)
        rows=prepare(tok);fitting=[r for r in rows if r["split"]=="train"]
        write_json(out/"actual-inputs-and-masks.json",rows)
        write_json(out/"comparator-replay.json",replay_comparators(tok,rows))
        launch.update(release_sha256=sha256(PACK/"release.json"),actual_inputs_sha256=sha256(out/"actual-inputs-and-masks.json"),
            comparator_replay_sha256=sha256(out/"comparator-replay.json"))
        if a.preflight_only:
            launch.update(status="preflight_complete",fit_sequence_tokens=sum(len(r["input_ids"]) for r in fitting)*8,
                fit_supervised_tokens=sum(r["supervised_tokens"] for r in fitting)*8,prefix_tokens={r["id"]:len(r["prefix_ids"]) for r in rows})
            write_json(out/"launch.json",launch);print(json.dumps(launch),flush=True);return
        preflight=json.loads((PACK/"preflight/launch.json").read_text())
        assert preflight["status"]=="preflight_complete" and preflight["actual_inputs_sha256"]==launch["actual_inputs_sha256"]
        assert a.gpu_uuid;launch["gpu"]=current_gpu(a.gpu_uuid)
        assert launch["gpu"]["name"]=="NVIDIA RTX PRO 6000 Blackwell Server Edition"
        os.environ["CUDA_VISIBLE_DEVICES"]=a.gpu_uuid;launch["model_verification"]=verify_model(cfg)
        current_gpu(a.gpu_uuid);write_json(out/"launch.json",launch);shutil.copyfile(__file__,out/"executed-runner.py")
        import torch
        from transformers import Qwen3_5ForCausalLM,GenerationConfig
        from country_persona.training_checks import adapter_snapshot,tensor_state_digest
        torch.manual_seed(42)
        model,loading=Qwen3_5ForCausalLM.from_pretrained(cfg["model_path"],local_files_only=True,dtype=torch.bfloat16,
            attn_implementation="sdpa",output_loading_info=True)
        assert not loading["missing_keys"] and not loading["mismatched_keys"] and not loading["error_msgs"]
        model=model.to("cuda:0")
        def owned():
            live=subprocess.check_output(["nvidia-smi","--query-compute-apps=gpu_uuid,pid","--format=csv,noheader,nounits"],text=True)
            assert {int(s.split(',')[1]) for s in live.splitlines() if s.split(',')[0].strip()==a.gpu_uuid}=={os.getpid()},"GPU ownership changed"
        owned();model=fresh_adapter(model);model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={"use_reentrant":False})
        result=train_loop(model,fitting,presentations=8,seed=42,learning_rate=5e-5,output=out,device="cuda:0")
        state=tensor_state_digest(adapter_snapshot(model));assert state==result["update"]["final_adapter_digest"]
        launch.update(production_optimizer_updates=result["steps"],training_result_sha256=sha256(out/"training-result.json"))
        decoder=GenerationConfig(do_sample=False,max_new_tokens=2048,use_cache=True,eos_token_id=tok.convert_tokens_to_ids("<|im_end|>"),pad_token_id=tok.pad_token_id)
        write_json(out/"decoder.json",decoder.to_dict())
        for spec in json.loads((PACK/"comparators.json").read_text()):
            assert decoder.to_dict()==json.loads((ROOT/spec["decoder"]).read_text())
        stages=[]
        while True:
            launch.update(status="awaiting_explicit_stage",completed_stages=stages);write_json(out/"launch.json",launch)
            print(json.dumps(dict(state="awaiting_explicit_stage",updates=48,stages=stages,idle_timeout_seconds=300)),flush=True)
            if not select.select([sys.stdin],[],[],300)[0]:break
            line=sys.stdin.readline()
            if not line:break
            command=json.loads(line)
            if command.get("operation")=="exit":break
            assert command.get("operation")=="evaluate"
            stage=command["stage"];assert stage==cfg["evaluation_stages"][len(stages)]
            if stages:
                prior=out/stages[-1];review=json.loads((prior/"inspection.json").read_text())
                assert review["complete_outputs_read"] is True and review["responses_sha256"]==sha256(prior/"responses.jsonl")
                assert review["rubric_sha256"]==sha256(PACK/"rubric.json")
            owned();assert tensor_state_digest(adapter_snapshot(model))==state
            selected=fitting if stage=="fitting" else [r for r in rows if r["split"]==stage]
            assert selected;dest=out/stage;dest.mkdir(exist_ok=False);model.eval()
            with (dest/"responses.jsonl").open('x') as f:
                for row in selected:
                    x=torch.tensor([row["prefix_ids"]],device="cuda:0");started=time.perf_counter()
                    with torch.inference_mode():y=model.generate(input_ids=x,attention_mask=torch.ones_like(x),generation_config=decoder)
                    torch.cuda.synchronize();ids=y[0,x.shape[1]:].tolist()
                    record=dict(id=row["id"],country=row["country"],arm="native48",split=row["split"],output_scope=row["output_scope"],
                        prefix_ids=row["prefix_ids"],prefix_sha256=row["prefix_sha256"],output_ids=ids,output_raw=tok.decode(ids,skip_special_tokens=False),
                        output_display=tok.decode(ids,skip_special_tokens=True),generated_tokens=len(ids),generation_seconds=time.perf_counter()-started,
                        at_cap=len(ids)==2048 and ids[-1]!=decoder.eos_token_id)
                    f.write(json.dumps(record,ensure_ascii=False)+"\n");f.flush();launch["production_generation_records"]+=1;write_json(out/"launch.json",launch)
            assert tensor_state_digest(adapter_snapshot(model))==state
            write_json(dest/"result.json",dict(answers=len(selected),responses_sha256=sha256(dest/"responses.jsonl"),rubric_sha256=sha256(PACK/"rubric.json"),quality="ungraded; read complete outputs and scope before next command"));stages.append(stage)
        launch.update(status="completed",process_state="exiting_normally",completed_stages=stages);write_json(out/"launch.json",launch)
    except Exception as exc:
        trace=out/"optimization.jsonl"
        if trace.exists():launch["production_optimizer_updates"]=len(trace.read_text().splitlines())
        launch.update(status="failed",exception=repr(exc),traceback=traceback.format_exc());write_json(out/"launch.json",launch);raise


if __name__=="__main__":main()
