"""Replay frozen judge prompts, tokenization, label margins, and scores."""
import argparse
import json
import math
from pathlib import Path

from transformers import AutoTokenizer

from run import HERE,digest,score,suite


def verify(path):
    launch=json.loads((path/"launch.json").read_text())
    complete=json.loads((path/"complete.json").read_text())
    trace=path/"predictions.jsonl"
    assert digest(trace)==complete["sha256"] and launch["optimizer_updates"]==0
    assert all(digest(HERE/name)==expected for name,expected in launch["sha256"].items())
    rows={r["id"]:r for r in map(json.loads,trace.read_text().splitlines())}
    assert len(rows)==complete["records"]==len(trace.read_text().splitlines())
    tok=AutoTokenizer.from_pretrained(launch["model"],local_files_only=True)
    lock=path/"reserve-lock.json"
    application=path/"application-lock.json"
    package=path/"package-lock.json"
    if any(Path(name).name=="field_panel.py" for name in launch["sha256"]):
        from field_panel import suite as field_suite,score as field_score
        plans=list(field_suite())
        scorer=field_score
    elif package.exists():
        from package_panel import suite as package_suite,score as package_score
        assert all(digest(Path(name))==expected for name,expected in json.loads(package.read_text()).items())
        plans=list(package_suite())
        scorer=package_score
    elif application.exists():
        from menu_review import suite as menu_suite,score as menu_score
        assert all(digest(Path(name))==expected for name,expected in json.loads(application.read_text()).items())
        plans=list(menu_suite())
        scorer=menu_score
    elif lock.exists():
        from transfer import suite as reserve_suite,score as reserve_score
        assert all(digest(HERE/name)==expected for name,expected in json.loads(lock.read_text()).items())
        plans=list(reserve_suite())
        scorer=reserve_score
    else:
        plans=list(suite())
        scorer=score
    assert set(rows)=={p["id"] for p in plans}
    for plan in plans:
        row=rows[plan["id"]]
        assert all(row[k]==v for k,v in plan.items())
        prompt=tok.apply_chat_template(plan["messages"],tokenize=False,add_generation_prompt=True,
                                       enable_thinking=False)
        assert tok.encode(prompt,add_special_tokens=False)==row["input_ids"]
        labels=[tok.encode(k,add_special_tokens=False)[0] for k in plan.get("labels","AB")]
        assert row["label_ids"]==labels
        assert len(row["label_logits"])==len(labels) and all(math.isfinite(v) for v in row["label_logits"])
    result=scorer(rows)
    assert json.loads((path/"metrics.json").read_text())==json.loads(json.dumps(result))
    return {"records":len(rows),"input_tokens":sum(len(r["input_ids"]) for r in rows.values()),
            "verified_totals":result["totals"]}


if __name__=="__main__":
    arg=argparse.ArgumentParser(description=__doc__)
    arg.add_argument("run",type=Path)
    print(json.dumps(verify(arg.parse_args().run),indent=2))
