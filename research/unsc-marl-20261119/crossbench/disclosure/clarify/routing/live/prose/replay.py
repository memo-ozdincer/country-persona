"""Verify the exact menu predictions and the dispatch paths they induce."""
import argparse
from hashlib import sha256
import json
from pathlib import Path

from transformers import AutoTokenizer

from study import CAP, score, suite
from episode import hashes


def verify(run):
    launch = json.loads((run/"launch.json").read_text())
    complete = json.loads((run/"complete.json").read_text())
    assert launch["optimizer_updates"]==complete["optimizer_updates"]==0
    assert launch["shared_locks"]==hashes()
    for path, expected in launch["sha256"].items():
        assert sha256(Path(path).read_bytes()).hexdigest()==expected
    trace = (run/"transcript.jsonl").read_bytes()
    assert complete["transcript_sha256"]==sha256(trace).hexdigest()
    rows = {row["id"]:row for row in map(json.loads,trace.splitlines())}
    projection = run/"projection-lock.json"
    reconciliation = run/"reconciliation-lock.json"
    field = run/"field-lock.json"
    if field.exists():
        from axis import suite as field_suite,score as field_score
        for path, expected in json.loads(field.read_text()).items():
            assert sha256((Path(__file__).parent/path).read_bytes()).hexdigest()==expected
        plans,_ = field_suite()
        scorer = field_score
    elif reconciliation.exists():
        from reconcile import suite as reconciled_suite,score as reconciled_score
        for path, expected in json.loads(reconciliation.read_text()).items():
            assert sha256((Path(__file__).parent/path).read_bytes()).hexdigest()==expected
        plans,_ = reconciled_suite()
        scorer = reconciled_score
    elif projection.exists():
        from project_rule import suite as projected_suite,score as projected_score
        expected = json.loads(projection.read_text())["project_rule.py"]
        assert sha256(Path(__file__).with_name("project_rule.py").read_bytes()).hexdigest()==expected
        plans,_ = projected_suite()
        scorer = projected_score
    else:
        plans,_ = suite()
        scorer = score
    assert plans.keys()==rows.keys()
    assert len(rows)==len(trace.splitlines())==complete["records"]==len(plans)
    tok=AutoTokenizer.from_pretrained(launch["model"],local_files_only=True)
    eos=tok.convert_tokens_to_ids("<|im_end|>")
    for id_, row in rows.items():
        expected=plans[id_]
        assert all(row[k]==v for k,v in expected.items())
        text=tok.apply_chat_template(row["messages"],tokenize=False,add_generation_prompt=True,enable_thinking=False)
        assert tok.encode(text,add_special_tokens=False)==row["input_ids"]
        tail=row["output_ids"]
        assert 0<len(tail)<=CAP and eos not in tail[:-1]
        assert (tail[-1]==eos)==row["ended"]
        assert row["ended"] or len(tail)==CAP
        assert tok.decode(tail,skip_special_tokens=True).strip()==row["output"]
    metrics=scorer(rows)
    assert json.loads(json.dumps(metrics))==json.loads((run/"metrics.json").read_text())
    return {"records":len(rows),"paths":len(metrics["paths"]),"exact_menus":sum(
            v["exact"] for v in metrics["menus"].values())}


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("run",type=Path)
    print(json.dumps(verify(p.parse_args().run),indent=2))
