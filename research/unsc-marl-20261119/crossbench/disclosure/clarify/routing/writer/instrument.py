"""Rerun the paired writer with its missing historical instrument supplied."""
import argparse
import json
from pathlib import Path

import run as base

original_suite = base.suite
original_sources = base.sources


def suite():
    scenario = json.loads((base.ROOT/"sanctions.json").read_text())
    historical = {field:scenario[field] for field in ("draft","meeting","date")}
    for row in original_suite():
        system, user = row["messages"]
        payload = json.loads(user["content"])
        payload["historical_instrument"] = historical
        yield {**row,"messages":[system,{"role":"user","content":json.dumps(
            payload,ensure_ascii=False,separators=(",",":"))}]}


def sources():
    return (*original_sources(), Path(__file__).resolve())


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("model",type=Path)
    p.add_argument("output",type=Path)
    args=p.parse_args()
    prepared = tuple(suite())
    base.suite = lambda: iter(prepared)
    base.sources = sources
    base.main(args.model,args.output)
