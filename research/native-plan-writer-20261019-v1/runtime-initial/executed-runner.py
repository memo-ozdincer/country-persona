"""One fresh native writer fit, with every stage explicitly inspected.

Starts with two source-only base answers. Application base, fitting, and each
adapter evaluation require separate stdin commands. There is no run queue.
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
from country_persona.scenario_sft import locked_runtime,ids_digest,train_loop,completion_loss
from country_persona.meeting_sequence import END
from run_aurora_qwen35_smoke import identity,current_gpu,verify_model
from run_scenario_sft import fresh_adapter

PACK=ROOT/"research/native-plan-writer-20261019-v1"


def prepare(tokenizer):
    rows=json.loads((PACK/"examples.json").read_text())
    assert len(rows)==8 and len({r["id"] for r in rows})==8
    for r in rows:
        assert all(END not in m["content"] and "<|im_start|>" not in m["content"] for m in r["messages"])
        prefix=tokenizer.apply_chat_template(r["messages"],tokenize=True,return_dict=False,
            add_generation_prompt=True,enable_thinking=False)
        assert len(prefix)+2048<=8192 and prefix.count(tokenizer.convert_tokens_to_ids(END))==2
        r.update(prefix_ids=prefix,prefix_sha256=ids_digest(prefix))
        if r["target"] is not None:
            tail=tokenizer.encode(r["target"]+END,add_special_tokens=False)
            whole=tokenizer.encode(tokenizer.decode(prefix,skip_special_tokens=False)+r["target"]+END,add_special_tokens=False)
            assert whole==prefix+tail
            r.update(input_ids=whole,labels=[-100]*len(prefix)+tail,prefix_tokens=len(prefix),supervised_tokens=len(tail))
    assert {r["episode"] for r in rows if r["split"]=="train"}=={"8923","9214"}
    assert {r["episode"] for r in rows if r["split"]!="train"}=={"8514"}
    return rows


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--gpu-uuid")
    parser.add_argument("--preflight-only",action="store_true")
    a=parser.parse_args();out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
    launch=dict(status="started",identity=identity(),runtime=locked_runtime(),output=str(out),
        code_sha256=sha256(Path(__file__)),production_generation_records=0,production_optimizer_updates=0)
    write_json(out/"launch.json",launch)
    try:
        release=json.loads((PACK/"release.json").read_text())
        for name,expected in release["files_sha256"].items():assert sha256(ROOT/name)==expected,name
        launch["release_sha256"]=sha256(PACK/"release.json")
        cfg=json.loads((PACK/"config.json").read_text())
        assert cfg["presentations"]==8 and cfg["updates"]==32
        from transformers import AutoTokenizer
        tok=AutoTokenizer.from_pretrained(cfg["model_path"],local_files_only=True)
        rows=prepare(tok);fitting=[r for r in rows if r["split"]=="train"]
        write_json(out/"actual-inputs-and-masks.json",rows)
        launch["actual_inputs_sha256"]=sha256(out/"actual-inputs-and-masks.json")
        if a.preflight_only:
            launch.update(status="preflight_complete",prefix_tokens={r["id"]:len(r["prefix_ids"]) for r in rows},
                fit_supervised_tokens=sum(r["supervised_tokens"] for r in fitting)*8,
                fit_sequence_tokens=sum(len(r["input_ids"]) for r in fitting)*8)
            write_json(out/"launch.json",launch);print(json.dumps(launch),flush=True);return
        assert a.gpu_uuid
        launch["gpu"]=current_gpu(a.gpu_uuid)
        assert launch["gpu"]["name"]=="NVIDIA RTX PRO 6000 Blackwell Server Edition"
        os.environ["CUDA_VISIBLE_DEVICES"]=a.gpu_uuid
        launch["model_verification"]=verify_model(cfg)
        current_gpu(a.gpu_uuid);write_json(out/"launch.json",launch)
        shutil.copyfile(__file__,out/"executed-runner.py")
        import torch
        from transformers import Qwen3_5ForCausalLM,GenerationConfig
        torch.manual_seed(42)
        model,loading=Qwen3_5ForCausalLM.from_pretrained(cfg["model_path"],local_files_only=True,
            dtype=torch.bfloat16,attn_implementation="sdpa",output_loading_info=True)
        assert not loading["missing_keys"] and not loading["mismatched_keys"] and not loading["error_msgs"]
        model=model.to("cuda:0").eval()
        decoder=GenerationConfig(do_sample=False,max_new_tokens=2048,use_cache=True,
            eos_token_id=tok.convert_tokens_to_ids(END),pad_token_id=tok.pad_token_id)
        write_json(out/"decoder.json",decoder.to_dict())
        stages=[];trained=False;trained_digest=None

        def evaluate(split,stage):
            dest=out/stage;dest.mkdir(exist_ok=False)
            selected=[r for r in rows if r["split"]==split]
            model.eval()
            with (dest/"responses.jsonl").open('x') as f:
                for row in selected:
                    x=torch.tensor([row["prefix_ids"]],device="cuda:0")
                    start=time.perf_counter()
                    with torch.inference_mode():
                        result=model.generate(input_ids=x,attention_mask=torch.ones_like(x),generation_config=decoder)
                    torch.cuda.synchronize();ids=result[0,x.shape[1]:].tolist()
                    record=dict(id=row["id"],country=row["country"],arm="adapter" if trained else "base",split=split,
                        prefix_sha256=row["prefix_sha256"],prefix_ids=row["prefix_ids"],output_ids=ids,
                        output_raw=tok.decode(ids,skip_special_tokens=False),output_display=tok.decode(ids,skip_special_tokens=True),
                        generated_tokens=len(ids),generation_seconds=time.perf_counter()-start,
                        at_cap=len(ids)==2048 and ids[-1]!=decoder.eos_token_id)
                    f.write(json.dumps(record,ensure_ascii=False)+"\n");f.flush()
                    launch["production_generation_records"]+=1;write_json(out/"launch.json",launch)
            write_json(dest/"result.json",dict(answers=len(selected),responses_sha256=sha256(dest/"responses.jsonl"),
                rubric_sha256=sha256(PACK/"rubric.json"),quality="ungraded; inspect all complete outputs"))
            stages.append(stage)

        def inspected(stage):
            path=out/stage/"inspection.json";d=json.loads(path.read_text())
            assert d["responses_sha256"]==sha256(out/stage/"responses.jsonl")
            assert d["rubric_sha256"]==sha256(PACK/"rubric.json") and d["complete_outputs_read"] is True
            return d

        evaluate("eval","base-source")
        while True:
            launch.update(status="awaiting_explicit_operation",completed_stages=stages)
            write_json(out/"launch.json",launch)
            print(json.dumps(dict(state="awaiting_explicit_operation",stages=stages,updates=launch["production_optimizer_updates"],idle_timeout_seconds=300)),flush=True)
            if not select.select([sys.stdin],[],[],300)[0]:break
            line=sys.stdin.readline()
            if not line:break
            command=json.loads(line);op=command.get("operation")
            if op=="exit":break
            live=subprocess.check_output(["nvidia-smi","--query-compute-apps=gpu_uuid,pid","--format=csv,noheader,nounits"],text=True)
            assert {int(s.split(',')[1]) for s in live.splitlines() if s.split(',')[0].strip()==a.gpu_uuid}=={os.getpid()},"GPU ownership changed"
            if op=="base_application":
                assert not trained and stages==["base-source"]
                inspected("base-source");evaluate("application_eval","base-application")
            elif op=="fit":
                assert not trained and stages==["base-source","base-application"]
                assert inspected("base-application")["decision"]=="run_one_fresh_32_update_native_fit"
                inspected("base-source")
                model=fresh_adapter(model)
                model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={"use_reentrant":False})
                result=train_loop(model,fitting,presentations=8,seed=42,learning_rate=5e-5,output=out,device="cuda:0")
                launch.update(production_optimizer_updates=result["steps"],training_result_sha256=sha256(out/"training-result.json"))
                trained=True
                from country_persona.training_checks import adapter_snapshot,tensor_state_digest
                trained_digest=tensor_state_digest(adapter_snapshot(model))
                assert trained_digest==result["update"]["final_adapter_digest"]
                write_json(out/"launch.json",launch)
            elif op=="evaluate":
                assert trained and command.get("split") in {"train","eval","application_eval"}
                split=command["split"]
                stage={"train":"adapter-fitting","eval":"adapter-source","application_eval":"adapter-application"}[split]
                assert stage not in stages
                if split!="train":inspected("adapter-fitting")
                if split=="application_eval":inspected("adapter-source")
                from country_persona.training_checks import adapter_snapshot,tensor_state_digest
                assert tensor_state_digest(adapter_snapshot(model))==trained_digest
                evaluate(split,stage)
                assert tensor_state_digest(adapter_snapshot(model))==trained_digest
            else:raise ValueError("Unknown explicit operation")
        launch.update(status="completed",process_state="exiting_normally",completed_stages=stages)
        write_json(out/"launch.json",launch)
    except Exception as exc:
        trace=out/"optimization.jsonl"
        if trace.exists():launch["production_optimizer_updates"]=len(trace.read_text().splitlines())
        launch.update(status="failed",exception=repr(exc),traceback=traceback.format_exc())
        write_json(out/"launch.json",launch);raise


if __name__=="__main__":main()
