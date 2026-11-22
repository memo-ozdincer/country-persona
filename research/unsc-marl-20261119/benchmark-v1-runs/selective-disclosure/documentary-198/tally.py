"""Test a smaller certificate explanation on all views that change settlement."""
import argparse
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
from unittest.mock import patch

import memo

HERE = Path(__file__).resolve().parent / "tally"


def plan():
    frozen = memo.s.read(HERE.parent / "plan.json")
    chosen = {}
    for events in frozen["pairs"].values():
        for episode in events:
            a, b = (episode[arm] for arm in ("fixed", "fitted"))
            left, right = (frozen["views"][view]["facts"]["checked_disposition"] for view in (a,b))
            if (left == "unresolved") != (right == "unresolved"):
                chosen[a] = True
                chosen[b] = True
    specs = {}
    for view in sorted(chosen):
        source = frozen["views"][view]
        cert = source["facts"]
        rule = cert["decision_rule"]
        prefix, sep, _ = source["fixed"].partition(rule)
        assert sep and prefix.strip()
        compiled = "\n\n".join((source["prefix"], prefix.strip()+" "+rule))
        counts = Counter("/".join(v["winners"]) for v in cert["compatible_completions"])
        observed = dict(checked_disposition=cert["checked_disposition"],
                        total_compatible_completions=sum(counts.values()),
                        winners_or_impasse_in_those_completions=counts)
        user = json.dumps(observed, ensure_ascii=False)
        system = (
            "Write only a concise warrant explanation for a fictional workshop memo in at most 30 words. "
            "Report the total compatible completions and explain what their outcome counts prove. "
            "Unresolved means the compatible completions lack a common disposition; impasse means all "
            "packages are infeasible in all compatible completions. If there are conflicting outcomes, name them. "
            "Described completions are possibilities rather than claimed actual cards. "
            "Use only the provided count data. Do not mention new grades, roles, or history."
        )
        specs[view] = dict(prefix=compiled, facts=cert, history=source["history"], counts=observed,
                           request=dict(id=view,max_output_tokens=63,
                                        messages=[dict(role="system",content=system),dict(role="user",content=user)]))
    assert len(specs) == 4
    paths = (Path(__file__), HERE/"protocol.md", HERE.parent/"plan.json", HERE.parent/"rubric.json")
    return dict(requests=[v["request"] for v in specs.values()], specs=specs,
                sha256={p.name:sha256(p.read_bytes()).hexdigest() for p in paths})


def run(mode):
    c = memo.load_collector()
    root = HERE/"evidence"
    with patch.multiple(c,HERE=HERE,EVIDENCE=root,plan=plan):
        if mode == "run":
            b = c.base()
            locked = plan()
            assert locked == memo.s.read(HERE/"plan.json")
            with patch.object(b.suite,"collect",c.collect), patch.object(b,"roster",return_value=locked["specs"]), patch.object(
                b,"HERE",HERE
            ), patch.object(b.suite.e,"HERE",memo.RELEASE):
                b.run(root)
        else:
            locked = plan()
            assert memo.s.read(root/"launch.json")["cases"] == list(locked["specs"])
            outputs = {}
            for req, art in c.rows():
                key = req["id"]
                info = locked["specs"][key]
                generated = art["text"]
                outputs[key] = dict(paragraph=generated, answer=info["prefix"]+"\n\n"+generated,
                                    facts=info["facts"],history=info["history"],counts=info["counts"],
                                    complete=art["termination"]=="complete" and len(generated.split())<=30,
                                    input_tokens=art["input_tokens"],output_tokens=art["output_tokens"])
            return outputs


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("plan","run","deck"))
    mode = parser.parse_args().mode
    if mode == "run":
        run(mode)
    else:
        print(json.dumps(plan() if mode == "plan" else run(mode), indent=2, ensure_ascii=False))
