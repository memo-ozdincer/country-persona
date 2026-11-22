"""Test inference of a role's full compatibility menu from a prose card."""
import argparse
from collections import Counter
from hashlib import sha256
from itertools import product
import json
import os
from pathlib import Path
import socket
import subprocess
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent))
from episode import CASES, judge, readout, serialize, source_paths
from environment import claim, record, routing_prior, terminal
from guard import guarded
from joint import restore
from sanctions import project

CAP = 72
SYSTEM = ("You are one delegate in a fictional post-vote workshop. Your private instructions determine which proposals "
          "you can accept in this simulation. Historical votes do not change those instructions.")
TASK = ('Evaluate all seven options independently under your private instruction. Return one JSON object with the key '
        '"accepts", listing the option IDs you can accept. Use only IDs A through G. Do not explain or add keys.')
CONVENERS = {"monitoring-team":"1267 Monitoring Team",
             "erc":"Emergency Relief Coordinator (ERC)","committee":"Sanctions Committee"}
TRACKS = {"renewed-review":"leave possible renewed review of a membership recommendation on the agenda",
          "briefings-only":"limit the agenda to briefings","hold-agenda":"hold the membership agenda"}
SEQUENCES = {"parallel":"work on a humanitarian pause in parallel",
             "pause-first":"address work on the humanitarian pause first"}


def label_card(case, role, variant):
    name = case["roles"][role]
    if name=="United Kingdom workshop delegate":
        return f"{name}/{variant}"
    return name


def describe(option):
    if "convener" in option:
        return (f"{CONVENERS[option['convener']]} convenes the review. Public reporting uses "
                f"{option['public_report']}. Interval {option['interval']}.")
    return f"{TRACKS[option['track']]}. {SEQUENCES[option['sequence']]}. Produce {option['product']}."


def suite():
    paths = source_paths()
    instructions = json.loads((HERE/"mandates.json").read_text())
    inputs, truth = {}, {}
    for family, variant, _ in CASES:
        case = json.loads(paths[family].read_text())
        for i, card in enumerate(case["variants"][variant]):
            role = case["roles"][i]
            name = label_card(case,i,variant)
            identifier = f"{family}/{name}"
            prompt = {"role":role,"scope":case["boundary"],"historical_evidence":case["historical"],
                      "private_instruction":instructions[family][name],
                      "packages":{o["id"]:describe(o) for o in case["options"]},"task":TASK}
            plan = {"id":identifier,"messages":[{"role":"system","content":SYSTEM},
                                                {"role":"user","content":serialize(prompt)}]}
            assert inputs.setdefault(identifier,plan)==plan
            mask = project(case["options"],card)
            assert truth.setdefault(identifier,mask)==mask
    return inputs, truth


def parse(text):
    def unique(pairs):
        ret = dict(pairs)
        if len(ret)!=len(pairs):
            raise ValueError("duplicate key")
        return ret
    try:
        payload = json.loads(text, object_pairs_hook=unique)
        if not isinstance(payload,dict) or set(payload)!={"accepts"} or not isinstance(payload["accepts"],list):
            return "invalid",0
        choices = payload["accepts"]
        if not all(isinstance(x,str) and x in tuple("ABCDEFG") for x in choices):
            return "invalid",0
        if len(set(choices))!=len(choices):
            return "invalid",0
        return "well_formed",sum(1 << "ABCDEFG".index(x) for x in choices)
    except (ValueError,TypeError):
        return "invalid",0


def dispatch(case, opening, observed, expected, arm, choose):
    """A reported sign reaches the public ledger only when the task validates it."""
    roles = case["roles"]
    labels = [o["id"] for o in case["options"]]
    full = (1<<len(labels))-1
    state, role = (0,0,0,0), 1
    history, rejected = [], []
    available = tuple(mask is not None for mask in observed)
    observed = tuple(mask if mask is not None else 0 for mask in observed)

    def offer(speaker, bit):
        nonlocal state
        letter = labels[bit.bit_length()-1]
        if not available[speaker]:
            rejected.append({"role":roles[speaker],"option":letter,"status":"invalid_menu"})
            return False
        raw = serialize({"option":letter,"stance":"accept" if observed[speaker]&bit else "exclude"})
        actual = bool(expected[speaker]&bit)
        status, endorsed = judge(raw,roles[speaker],letter,actual,f"claim-{len(history)+1}")
        if endorsed is None:
            rejected.append({"role":roles[speaker],"option":letter,"status":status})
            return False
        state = record(state,speaker,bit,actual)
        history.append(endorsed)
        return True

    for i, letter in enumerate(opening):
        offer(i,1<<labels.index(letter))
    steps = 0
    for k in range(len(labels)):
        if terminal(state,full):
            break
        steps += 1
        if arm=="script":
            bit = claim(observed[role],state,role,k,full,flex=True)
            predict = record(state,role,bit,bool(bit&observed[role])) if bit else state
            who = routing_prior(observed[role],predict,role,full) if bit else 1-role
        else:
            _, actions, action = choose(observed,state,role,k,full)
            bit, _, who = actions[action] if actions else (0,state,1-role)
        role = who if bit and offer(role,bit) else 1-role
    proof = readout(labels,roles,history)
    return {"state":proof["state"],"claims":history,"rejected":rejected,"steps":steps,
            "proof":proof}


def score(rows):
    _, truth = suite()
    observed = {}
    extraction = {}
    for name, value in rows.items():
        status, mask = parse(value["output"])
        observed[name] = mask if status=="well_formed" else None
        extraction[name] = {"status":status,"estimated":mask,"reference":truth[name],
                            "exact":status=="well_formed" and mask==truth[name],
                            "false_accepts":(mask&~truth[name]).bit_count(),
                            "missed_accepts":(truth[name]&~mask).bit_count()}
    assert observed.keys()==truth.keys()
    source = source_paths()
    choose = guarded(restore(json.loads(source["policy"].read_text())))
    result, counts = {},Counter()
    for family,variant,selected in CASES:
        case = json.loads(source[family].read_text())
        ids = tuple(f"{family}/{label_card(case,i,variant)}" for i in (0,1))
        real, inferred = (tuple(ref[name] for name in ids) for ref in (truth,observed))
        options = [x["id"] for x in case["options"]]
        openings = product(*([letter for i,letter in enumerate(options) if mask&(1<<i)] for mask in real))
        for first in openings:
            for arm in ("script","learned"):
                typed = dispatch(case,first,real,real,arm,choose)
                prose = dispatch(case,first,inferred,real,arm,choose)
                key = f"{family}/{variant}/{''.join(first)}/{arm}"
                result[key] = {"typed":typed,"prose":prose,"live_opening":list(first)==list(selected)}
                target = "AGREEMENT_POSSIBLE" if variant=="overlap" else "IMPASSE"
                counts[family,variant,arm,"total"] += 1
                counts[family,variant,arm,"typed_certified"] += typed["state"]==target
                counts[family,variant,arm,"prose_certified"] += prose["state"]==target
                counts[family,variant,arm,"prose_rejections"] += len(prose["rejected"])
    return {"menus":extraction,"openings":{"/".join(k):v for k,v in counts.items()},"paths":result}


def main(model_path, output):
    import torch
    import transformers
    from transformers import AutoModelForCausalLM, AutoTokenizer

    plans, _ = suite()
    rows = list(plans.values())
    output.mkdir()
    torch.set_num_threads(8)
    torch.set_num_interop_threads(1)
    sources = [*source_paths().values(),HERE/"mandates.json",Path(__file__).resolve()]
    from episode import hashes
    receipt = {"host":socket.gethostname(),"pid":os.getpid(),"device":"CPU","gpu_uuids":[],
               "process_start":subprocess.check_output(["ps","-o","lstart=","-p",str(os.getpid())],text=True).strip(),
               "command":[sys.executable,*sys.argv],"run_directory":str(output.resolve()),
               "model":str(model_path.resolve()),"torch":torch.__version__,"transformers":transformers.__version__,
               "optimizer_updates":0,"shared_locks":hashes(),
               "sha256":{str(p):sha256(p.read_bytes()).hexdigest() for p in sources}}
    (output/"launch.json").write_text(json.dumps(receipt,indent=2)+"\n")
    tok = AutoTokenizer.from_pretrained(model_path,local_files_only=True,padding_side="left")
    eos = tok.convert_tokens_to_ids("<|im_end|>")
    model = AutoModelForCausalLM.from_pretrained(
        model_path,local_files_only=True,dtype=torch.bfloat16,attn_implementation="sdpa").eval()
    ids = [tok.encode(tok.apply_chat_template(row["messages"],tokenize=False,
                    add_generation_prompt=True,enable_thinking=False),add_special_tokens=False) for row in rows]
    assert max(map(len,ids))+CAP<4096
    inputs = tok.pad({"input_ids":ids},return_tensors="pt")
    with torch.inference_mode():
        predictions = model.generate(**inputs,do_sample=False,max_new_tokens=CAP,eos_token_id=eos,
                                     pad_token_id=tok.pad_token_id)
    answers = {}
    trace = output/"transcript.jsonl"
    with trace.open("x") as f:
        for row,prefix,tail in zip(rows,ids,predictions[:,inputs.input_ids.shape[-1]:].tolist(),strict=True):
            if eos in tail:
                tail=tail[:tail.index(eos)+1]
            text=tok.decode(tail,skip_special_tokens=True).strip()
            entry={**row,"input_ids":prefix,"output_ids":tail,"output":text,"ended":tail[-1]==eos}
            answers[row["id"]]=entry
            f.write(serialize(entry)+"\n")
    result=score(answers)
    (output/"metrics.json").write_text(json.dumps(result,indent=2)+"\n")
    (output/"complete.json").write_text(serialize({"records":len(answers),
        "transcript_sha256":sha256(trace.read_bytes()).hexdigest(),"optimizer_updates":0})+"\n")
    print(serialize(result["menus"]),flush=True)


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("model",type=Path)
    p.add_argument("output",type=Path)
    args=p.parse_args()
    main(args.model,args.output)
