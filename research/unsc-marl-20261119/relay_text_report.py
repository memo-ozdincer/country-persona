"""Replay the language action heads and isolate communication and chair effects."""
from hashlib import sha256
import json
from pathlib import Path
import sys

import torch

import relay_readout
import relay_text_context as context
import relay_text_train as shared


def read_locked(directory,kind):
    metadata=json.loads((directory/f"{kind}-launch.json").read_text())
    assert metadata["torch"]==torch.__version__
    for name,value in metadata["sha256"].items():
        assert sha256((shared.text.HERE/name).read_bytes()).hexdigest()==value,name
    return json.loads((directory/f"{kind}.json").read_text())


def report(directory):
    torch.set_num_threads(1)
    cache=shared.text.read(directory)
    trained=read_locked(directory,"head")
    conditional=read_locked(directory,"context")
    policy=context.Conditional()
    policy.load_state_dict({k:torch.tensor(v) for k,v in conditional["parameters"].items()})
    replay={}
    with torch.no_grad():
        original=shared.assess(cache,shared.Head())
        assert json.loads(json.dumps(original))==trained["base"]
        for kind, entry in trained["arms"].items():
            head=shared.Head()
            head.load_state_dict({"offset":torch.tensor(entry["head"])})
            frozen=shared.assess(cache,head)
            assert json.loads(json.dumps(frozen))==entry["after"]
            replay[kind]=len(entry["updates"])

        def transform(mode):
            variants={}
            for key,row in cache.items():
                _,phase,left,right,_=key
                adapted=policy.logits(key,row).tolist()
                scores=row["scores"]
                if phase!=3 and mode in ("communication_only","both","fixed_rule_with_learned_messages"):
                    scores=adapted
                elif phase==3 and mode in ("chair_only","both"):
                    scores=adapted
                elif phase==3 and left and right and mode.startswith("fixed_rule"):
                    shared_candidate=bool(left&right)
                    scores=[score if (i!=len(scores)-1)==shared_candidate else -10000.
                            for i,score in enumerate(scores)]
                variants[key]={**row,"scores":scores}
            return shared.assess(variants,shared.Head())

        decomposed={mode:transform(mode) for mode in (
            "communication_only","chair_only","both","fixed_rule_with_base_messages",
            "fixed_rule_with_learned_messages")}
        assert json.loads(json.dumps(decomposed["both"]))==conditional["after"]
    summaries={}
    all_arms={"base":original,"flat_outcome":trained["arms"]["outcome"]["after"],
              "flat_warranted":trained["arms"]["warranted"]["after"],**decomposed}
    for label,data in all_arms.items():
        summaries[label]={name:{key:{
            signal:sum(r[signal] for r in values)
            for signal in ("valid","warranted","both_sources","messages")}
            for key,values in arms.items()} for name,arms in data.items()}
    proof_input={"arms":{label:{"after":rows} for label,rows in all_arms.items()
                         if label in ("base","flat_warranted","both","fixed_rule_with_learned_messages")}}
    return {"scope":"Reload cached Qwen inference, flat heads, and conditional head. Independently gate learned communication and chair components. The fixed rule changes just the impasse category after two complete reported cards.",
            "qwen_records":len(cache),"flat_update_records":replay,
            "conditional_updates":len(conditional["updates"]),"exact_checkpoint_replay":True,
            "scores":summaries,"transcripts":relay_readout.evaluate(proof_input)}


if __name__=="__main__":
    print(json.dumps(report(Path(sys.argv[1])),indent=2))
