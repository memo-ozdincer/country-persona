"""Check exact shared prompts and targets against the previously audited mixed fit."""
from collections import Counter
import argparse
from hashlib import sha256
import json
from math import isfinite

from positive_fit import HERE, MIX, EPOCHS, base, plan, read


def rows(path):
    return list(map(json.loads,path.read_text().splitlines()))


def run():
    spec=plan()
    assert spec==read(HERE/"plan.json")
    out=HERE/"evidence"
    receipt=read(out/"complete.json")
    assert all(sha256((out/k).read_bytes()).hexdigest()==digest for k,digest in receipt["sha256"].items())
    old={r["case"]:r for r in rows(MIX/"evidence/updates.jsonl")}
    histories=rows(out/"updates.jsonl")
    expected={r["id"]:EPOCHS for r in spec["training"]}
    assert Counter(r["case"] for r in histories)==expected
    assert receipt["updates"]==len(histories)
    assert read(MIX/"audit-fit.json")["held_prompts_excluded"]==len(spec["held"])
    for order,row in enumerate(histories,1):
        comparator=old[row["case"]]
        assert row["step"]==order and isfinite(row["loss"])
        assert comparator["prompt_ids"]==row["prompt_ids"]
        assert comparator["target_ids"]==row["target_ids"]
        assert len(row["gradients"])==8 and all(isfinite(v) for v in row["gradients"].values())
        assert any(v>0 for v in row["gradients"].values())
    from tokenizers import Tokenizer
    tokenizer=Tokenizer.from_file(str(base.MODEL/"tokenizer.json"))
    eos=tokenizer.token_to_id("<|im_end|>")
    prior=rows(MIX/"evidence/frozen.jsonl")
    outputs={}
    for mode in ("frozen","adapted"):
        outputs[mode]={}
        for before,after in zip(prior,rows(out/f"{mode}.jsonl"),strict=True):
            assert before["id"]==after["id"] and before["input_ids"]==after["input_ids"]
            assert eos not in after["output_ids"][:-1]
            assert bool(after["output_ids"] and after["output_ids"][-1]==eos)==(
                after["reply"]["termination"]=="complete")
            assert tokenizer.decode(after["output_ids"],skip_special_tokens=True).strip()==after["reply"]["text"]
            assert len(after["input_ids"])==after["reply"]["input_tokens"]
            assert len(after["output_ids"])==after["reply"]["output_tokens"]
            if mode=="frozen":
                assert before==after
            outputs[mode][after["id"]]=after["reply"]
    audit={"updates":len(histories),"audited_exposures":expected,
            "assistant_token_targets":sum(len(r["target_ids"]) for r in histories),
            "verified_held_prompts":len(spec["held"]),"all_held_output_token_replays":2*len(spec["held"])}
    return audit, {"receipt":receipt,"outputs":outputs}


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--verified",action="store_true")
    audit,verified=run()
    print(json.dumps(verified if p.parse_args().verified else audit,ensure_ascii=False,indent=2))
