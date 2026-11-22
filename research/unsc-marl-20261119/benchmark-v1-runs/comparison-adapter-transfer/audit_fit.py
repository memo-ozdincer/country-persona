"""Verify the training split, token alignment, and exposure counts from the run."""
from collections import Counter
from math import isfinite
import json
from pathlib import Path

from train_writer import encode, EPOCHS, HERE, MODEL, read


def run():
    from transformers import AutoTokenizer
    plan=read(HERE/"plan.json")
    records=list(map(json.loads,(HERE/"evidence/updates.jsonl").read_text().splitlines()))
    assert [r["step"] for r in records]==list(range(1,len(records)+1))
    expected={r["id"]:r for r in plan["training"]}
    assert Counter(r["case"] for r in records)=={key:EPOCHS for key in expected}
    tok=AutoTokenizer.from_pretrained(MODEL,local_files_only=True)
    eos=tok.convert_tokens_to_ids("<|im_end|>")
    held={tuple(encode(tok,r["messages"])) for r in plan["held"].values()}
    for update in records:
        row=expected[update["case"]]
        prompt=encode(tok,[{"role":"system","content":plan["system"]},
                           {"role":"user","content":json.dumps(row["payload"],ensure_ascii=False)}])
        suffix=tok.encode(row["target"],add_special_tokens=False)+[eos]
        assert prompt==update["prompt_ids"] and suffix==update["target_ids"]
        assert tuple(prompt) not in held
        assert isfinite(update["loss"])
        assert len(update["gradients"])==8 and any(v>0 for v in update["gradients"].values())
        assert all(isfinite(v) for v in update["gradients"].values())
    return {"updates":len(records),"held_prompts_excluded":len(held),"exposures":dict(Counter(r["case"] for r in records)),
            "assistant_token_targets":sum(len(r["target_ids"]) for r in records)}


if __name__=="__main__":
    print(json.dumps(run(),indent=2))
