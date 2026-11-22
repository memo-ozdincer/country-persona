"""Test family-only instructions and an explicit rule for missing evidence."""
import argparse
from contextlib import contextmanager
from hashlib import sha256
import json
from pathlib import Path
from unittest.mock import patch

import relay_final_memo as baseline

BASE_SUITE=baseline.suite
BASE_SOURCES=baseline.sources
EXTRA=(
    " UNRESOLVED means no package incompatibility or scheduling failure was established. "
    "Use only delivered cards to establish a holder's position. Name the holder whose card did not arrive, "
    "request it, and leave the decision pending. Keep that evidence gap separate from the historical record."
)
REMOVE={
    "mali":"For Myanmar include the authority, reporting duty, and deadline. ",
    "myanmar":"For Mali include both draft symbols, reasons for failure and tallies. ",
}


def suite():
    for row in BASE_SUITE():
        if row["arm"]!="withheld_far":
            continue
        original=json.loads(row["messages"][1]["content"])
        family=row["family"]
        assert REMOVE[family] in original["instruction"]
        clean=original["instruction"].replace(REMOVE[family],"")
        for name,append in (("family_only",""),("explicit_evidence_gap",EXTRA)):
            messages=[row["messages"][0],{"role":"user","content":json.dumps(
                {**original,"instruction":clean+append},ensure_ascii=False)}]
            yield {**row,"id":f"{family}/{name}","arm":name,"messages":messages}


def sources():
    return {**BASE_SOURCES(),Path(__file__).name:sha256(Path(__file__).read_bytes()).hexdigest()}


@contextmanager
def enabled():
    with patch.object(baseline,"suite",new=suite),patch.object(baseline,"sources",new=sources):
        yield


if __name__=="__main__":
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument("directory",type=Path)
    cli.add_argument("--model",type=Path,required=True)
    args=cli.parse_args()
    with enabled():
        baseline.run(args.model,args.directory)
