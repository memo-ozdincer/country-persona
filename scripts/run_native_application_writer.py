"""One inspected fresh five-target/40-update writer experiment.

Replays old WPS comparators; generates a new Brazil base control, then waits for
an explicit fitting decision. Every later evaluation is a separate operation.
"""
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
from country_persona.scenario_sft import locked_runtime,ids_digest,train_loop
from country_persona.meeting_sequence import END
from run_aurora_qwen35_smoke import identity,current_gpu,verify_model
from run_scenario_sft import fresh_adapter

PACK=ROOT/"research/native-application-writer-20261019-v1"


def prepare(tok):
    cfg=json.loads((PACK/"config.json").read_text());rows=json.loads((PACK/"examples.json").read_text())
    assert len(rows)==len(cfg["case_countries"]) and {r["id"]:r["country"] for r in rows}==cfg["case_countries"]
    for r in rows:
        assert r["messages"][-1]["content"].endswith(r["country"]+" national delegation.")
        assert all(END not in m["content"] and "<|im_start|>" not in m["content"] for m in r["messages"])
        prefix=tok.apply_chat_template(r["messages"],tokenize=True,return_dict=False,add_generation_prompt=True,enable_thinking=False)
        assert len(prefix)+2048<=8192 and prefix.count(tok.convert_tokens_to_ids(END))==2
        r.update(prefix_ids=prefix,prefix_sha256=ids_digest(prefix))
        if r["target"] is not None:
            tail=tok.encode(r["target"]+END,add_special_tokens=False)
            whole=tok.encode(tok.decode(prefix,skip_special_tokens=False)+r["target"]+END,add_special_tokens=False)
            assert whole==prefix+tail
            r.update(input_ids=whole,labels=[-100]*len(prefix)+tail,prefix_tokens=len(prefix),supervised_tokens=len(tail))
    assert {r["episode"] for r in rows if r["split"]=="train"}=={"8923","9214"}
    assert {r["id"] for r in rows if r["split"]=="train"}==set(cfg["fitting_ids"])
    assert all(r["target"] is None for r in rows if r["split"]!="train")
    return rows


def replay_comparators(tok,rows):
    byid={r["id"]:r for r in rows};spec=json.loads((PACK/"comparators.json").read_text());result={}
    for name,item in spec.items():
        records=[json.loads(s) for s in (ROOT/item["responses"]).read_text().splitlines()]
        assert sha256(ROOT/item["responses"])==item["responses_sha256"]
        assert sha256(ROOT/item["inspection"])==item["inspection_sha256"]
        actual={r["id"]:r for r in json.loads((ROOT/item["actual_inputs"]).read_text())}
        for r in records:
            row=byid[r["id"]];assert actual[r["id"]]["messages"]==row["messages"]
            assert r["prefix_sha256"]==row["prefix_sha256"]
            assert tok.decode(r["output_ids"],skip_special_tokens=False)==r["output_raw"]
        launch=json.loads((ROOT/item["launch"]).read_text())
        assert launch["runtime"]==locked_runtime() and launch["gpu"]["name"]=="NVIDIA RTX PRO 6000 Blackwell Server Edition"
        result[name]=dict(records=len(records),responses_sha256=item["responses_sha256"],inspection_sha256=item["inspection_sha256"],
                          actual_prefixes_and_outputs_replayed=True,new_generations=0)
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--output",type=Path,required=True)
    p.add_argument("--gpu-uuid");p.add_argument("--preflight-only",action="store_true");a=p.parse_args()
    out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
    launch=dict(status="started",identity=identity(),runtime=locked_runtime(),output=str(out),code_sha256=sha256(Path(__file__)),
                production_generation_records=0,production_optimizer_updates=0)
    write_json(out/"launch.json",launch)
    try:
        release=json.loads((PACK/"release.json").read_text())
        for path,expected in release["files_sha256"].items():assert sha256(ROOT/path)==expected,path
        launch["release_sha256"]=sha256(PACK/"release.json")
        cfg=json.loads((PACK/"config.json").read_text());assert cfg["presentations"]==8 and cfg["updates"]==40
        from transformers import AutoTokenizer
        tok=AutoTokenizer.from_pretrained(cfg["model_path"],local_files_only=True)
        rows=prepare(tok);fitting=[r for r in rows if r["split"]=="train"]
        write_json(out/"actual-inputs-and-masks.json",rows)
        write_json(out/"comparator-replay.json",replay_comparators(tok,rows))
        launch.update(actual_inputs_sha256=sha256(out/"actual-inputs-and-masks.json"),comparator_replay_sha256=sha256(out/"comparator-replay.json"))
        if a.preflight_only:
            launch.update(status="preflight_complete",fit_sequence_tokens=sum(len(r["input_ids"]) for r in fitting)*8,
                          fit_supervised_tokens=sum(r["supervised_tokens"] for r in fitting)*8,prefix_tokens={r["id"]:len(r["prefix_ids"]) for r in rows})
            write_json(out/"launch.json",launch);print(json.dumps(launch),flush=True);return
        assert a.gpu_uuid;launch["gpu"]=current_gpu(a.gpu_uuid)
        assert launch["gpu"]["name"]=="NVIDIA RTX PRO 6000 Blackwell Server Edition"
        os.environ["CUDA_VISIBLE_DEVICES"]=a.gpu_uuid;launch["model_verification"]=verify_model(cfg)
        current_gpu(a.gpu_uuid);write_json(out/"launch.json",launch);shutil.copyfile(__file__,out/"executed-runner.py")
        import torch
        from transformers import Qwen3_5ForCausalLM,GenerationConfig
        torch.manual_seed(42)
        model,loading=Qwen3_5ForCausalLM.from_pretrained(cfg["model_path"],local_files_only=True,dtype=torch.bfloat16,
            attn_implementation="sdpa",output_loading_info=True)
        assert not loading["missing_keys"] and not loading["mismatched_keys"] and not loading["error_msgs"]
        model=model.to("cuda:0").eval()
        decoder=GenerationConfig(do_sample=False,max_new_tokens=2048,use_cache=True,eos_token_id=tok.convert_tokens_to_ids(END),pad_token_id=tok.pad_token_id)
        write_json(out/"decoder.json",decoder.to_dict())
        for item in json.loads((PACK/"comparators.json").read_text()).values():assert json.loads((ROOT/item["decoder"]).read_text())==decoder.to_dict()
        stages=[];trained=False;state=None

        def evaluate(split,stage):
            dest=out/stage;dest.mkdir(exist_ok=False);selected=[r for r in rows if r["split"]==split];assert selected
            model.eval()
            with (dest/"responses.jsonl").open('x') as f:
                for r in selected:
                    x=torch.tensor([r["prefix_ids"]],device="cuda:0");start=time.perf_counter()
                    with torch.inference_mode():generated=model.generate(input_ids=x,attention_mask=torch.ones_like(x),generation_config=decoder)
                    torch.cuda.synchronize();ids=generated[0,x.shape[1]:].tolist()
                    record=dict(id=r["id"],country=r["country"],split=split,arm="adapter40" if trained else "base",prefix_ids=r["prefix_ids"],
                        prefix_sha256=r["prefix_sha256"],output_ids=ids,output_raw=tok.decode(ids,skip_special_tokens=False),output_display=tok.decode(ids,skip_special_tokens=True),
                        generated_tokens=len(ids),generation_seconds=time.perf_counter()-start,at_cap=len(ids)==2048 and ids[-1]!=decoder.eos_token_id)
                    f.write(json.dumps(record,ensure_ascii=False)+"\n");f.flush();launch["production_generation_records"]+=1;write_json(out/"launch.json",launch)
            write_json(dest/"result.json",dict(answers=len(selected),responses_sha256=sha256(dest/"responses.jsonl"),rubric_sha256=sha256(PACK/"rubric.json"),quality="ungraded; read complete outputs"));stages.append(stage)

        def inspected(stage):
            d=json.loads((out/stage/"inspection.json").read_text())
            assert d["complete_outputs_read"] is True and d["responses_sha256"]==sha256(out/stage/"responses.jsonl")
            assert d["rubric_sha256"]==sha256(PACK/"rubric.json")
            return d

        evaluate("new_eval","base-new")
        while True:
            launch.update(status="awaiting_explicit_operation",completed_stages=stages);write_json(out/"launch.json",launch)
            print(json.dumps(dict(state="awaiting_explicit_operation",stages=stages,updates=launch["production_optimizer_updates"],idle_timeout_seconds=300)),flush=True)
            if not select.select([sys.stdin],[],[],300)[0]:break
            line=sys.stdin.readline()
            if not line:break
            command=json.loads(line);op=command.get("operation")
            if op=="exit":break
            live=subprocess.check_output(["nvidia-smi","--query-compute-apps=gpu_uuid,pid","--format=csv,noheader,nounits"],text=True)
            assert {int(s.split(',')[1]) for s in live.splitlines() if s.split(',')[0].strip()==a.gpu_uuid}=={os.getpid()},"GPU ownership changed"
            if op=="fit":
                assert not trained and stages==["base-new"] and inspected("base-new")["decision"]=="run_one_fresh40_fit"
                model=fresh_adapter(model);model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={"use_reentrant":False})
                result=train_loop(model,fitting,presentations=8,seed=42,learning_rate=5e-5,output=out,device="cuda:0")
                from country_persona.training_checks import adapter_snapshot,tensor_state_digest
                state=tensor_state_digest(adapter_snapshot(model));assert state==result["update"]["final_adapter_digest"]
                launch.update(production_optimizer_updates=result["steps"],training_result_sha256=sha256(out/"training-result.json"));trained=True
                write_json(out/"launch.json",launch)
            elif op=="evaluate":
                split=command.get("split");assert trained and split in {"train","source_eval","application_eval","new_eval"}
                stage={"train":"adapter-fitting","source_eval":"adapter-source","application_eval":"adapter-application","new_eval":"adapter-new"}[split]
                assert stage not in stages
                if split!="train":inspected("adapter-fitting")
                if split=="application_eval":inspected("adapter-source")
                if split=="new_eval":inspected("adapter-application")
                from country_persona.training_checks import adapter_snapshot,tensor_state_digest
                assert tensor_state_digest(adapter_snapshot(model))==state;evaluate(split,stage);assert tensor_state_digest(adapter_snapshot(model))==state
            else:raise ValueError("Unknown explicit operation")
        launch.update(status="completed",process_state="exiting_normally",completed_stages=stages);write_json(out/"launch.json",launch)
    except Exception as exc:
        trace=out/"optimization.jsonl"
        if trace.exists():launch["production_optimizer_updates"]=len(trace.read_text().splitlines())
        launch.update(status="failed",exception=repr(exc),traceback=traceback.format_exc());write_json(out/"launch.json",launch);raise


if __name__=="__main__":main()
