"""Render final records from the verified incomplete-menu handoff traces."""
import argparse
import json
from pathlib import Path

from package_panel import inputs
from compose import render


def records(artifact):
    cases={family:case for family,case,_ in inputs()}
    out={}
    for name,row in artifact["traces"].items():
        family,arm,opening=name.split("/")
        if arm not in ("script","learned"):
            continue
        case=cases[family]
        proof=row["readout"]
        text=render(case,row["claims"],proof)
        out[name]={"record":text,"words":len(text.split()),"status":proof["state"]}
    return out


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("trace",type=Path)
    a=p.parse_args()
    print(json.dumps(records(json.loads(a.trace.read_text())),indent=2,ensure_ascii=False))
