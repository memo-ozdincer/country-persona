"""Repeat a locked four-anchor slice with a consistent citation-address prompt."""
import argparse
from pathlib import Path
import re
import sys
from unittest.mock import patch

HERE=Path(__file__).resolve().parent
BEFORE=HERE.parent/"indexed-judge-calibration"
sys.path.insert(0,str(BEFORE))
import indexed

live=indexed.live
e=indexed.e
suite=live.suite
OUT=HERE/"evidence"
SELECT={
    "final": {e.checksum(["judge-anchor","full-myanmar"])[:16],"97fc4b1348810bae"},
    "process": {"process-325fda471a060851","process-0bc56df3502caa70"},
}
BASE= indexed.indexed


def reword(original,mode):
    packet,loc,names=BASE(original,mode)
    system=original["messages"][0]["content"]
    if mode=="final":
        system=re.sub(r"5\. Cite contiguous, exact text[^\n]+",
                      "5. Cite the printed passage IDs from the answer and identified evidence blocks.",system)
        system=system.replace('"quote":"exact span"','"quote":"printed source passage ID"')
        system=system.replace('"response":"exact span or empty for an omission"',
                              '"response":"printed answer passage ID or empty for an omission"')
        system=system.replace('"response":"exact span or empty"',
                              '"response":"printed answer passage ID or empty"')
    else:
        system=system.replace('exact contiguous `quote`','printed passage ID in `quote`')
        system=system.replace("Use at most one quote per turn per rating.",
                              "Use at most one passage ID or range per turn per rating.")
        system=system.replace("Use one\nexact quote per turn and stance.",
                              "Use one\npassage ID or range per turn and stance.")
    assert "exact contiguous `quote`" not in system
    return {"messages":[{"role":"system","content":system+indexed.INDEX_INSTRUCTIONS},
                        packet["messages"][-1]],"max_output_tokens":packet["max_output_tokens"]},loc,names


def fixtures():
    original={"final":live.anchors(),"process":live.process_anchors()}
    selected={mode:{key:item for key,item in items.items() if key in SELECT[mode]}
              for mode,items in original.items()}
    assert all(set(selected[mode])==keys for mode,keys in SELECT.items())
    return selected


def requests():
    groups={}
    for mode,rows in indexed.ORIGINAL().items():
        groups[mode]=[row | {"request":reword(row["request"],mode)[0]} for row in rows if row["id"] in SELECT[mode]]
    return groups


def plan():
    files=(Path(__file__),HERE/"protocol.md",BEFORE/"indexed.py",BEFORE/"plan.json")
    return {"selected":{k:sorted(v) for k,v in SELECT.items()},
            "release":suite.pin(live.prior.RELEASE/"release.json"),
            "inputs":{str(p.relative_to(HERE.parent)):suite.pin(p) for p in files},
            "request_hashes":{k:[e.checksum(r["request"]) for r in v] for k,v in requests().items()}}


def replay(directory,rows):
    selected=fixtures()
    with patch("calibrate.anchors",return_value=selected["final"]),patch("calibrate.process_anchors",
            return_value=selected["process"]),patch.object(live,"anchors",return_value=selected["final"]),patch.object(
            live,"process_anchors",return_value=selected["process"]),patch.object(indexed,"indexed",side_effect=reword):
        return indexed.replay(directory,rows)


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode",choices=("plan","run","verify","replay"))
    p.add_argument("--output",type=Path)
    args=p.parse_args()
    spec=plan()
    if args.mode!="plan":
        assert spec==e.read(HERE/"plan.json")
    if args.mode=="plan":
        e.emit(spec)
    elif args.mode=="replay":
        e.emit(replay(args.output,live.prior.report.load(OUT/"tokens.jsonl")))
    else:
        with patch.object(live,"HERE",HERE),patch.object(live,"OUT",OUT),patch.object(live,"requests",side_effect=requests):
            if args.mode=="run":
                live.run()
            else:
                e.emit(live.verify(live.prior.report.load(OUT/"tokens.jsonl")))
