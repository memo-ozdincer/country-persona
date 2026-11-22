"""Put the consultation comparison first, holding routed evidence fixed."""
import argparse
from contextlib import contextmanager
from hashlib import sha256
import json
from pathlib import Path
from unittest.mock import patch

import source_route_memos as base

DEFAULT_SUITE = base.suite
DEFAULT_LOCKS = base.locks
INSTRUCTION = (
    "Write a factual chair's memo in at most 120 words. Begin with one sentence on consultation or the "
    "Personal Envoy. State any common ground and each delegation's different condition with a source ID "
    "for each. If either side's position on this point is missing, say the available evidence is insufficient "
    "to establish shared ground. Then record the draft, both sponsors, the full vote including abstentions "
    "and cause, proposed measures, and each delegation's reason and caveat. Include a clearly hypothetical "
    "next step only if space remains. Use source IDs and no headings."
)


def suite():
    for row in DEFAULT_SUITE():
        content = json.loads(row["messages"][-1]["content"])
        assert content["working_text"] == []
        payload = {**content,"task":INSTRUCTION}
        yield {**row,"messages":[row["messages"][0],
                                  {"role":"user","content":json.dumps(payload,ensure_ascii=False)}]}


def locks():
    return {**DEFAULT_LOCKS(),Path(__file__).name:sha256(Path(__file__).read_bytes()).hexdigest()}


@contextmanager
def configured():
    with patch.object(base,"suite",new=suite), patch.object(base,"locks",new=locks):
        yield


if __name__=="__main__":
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument("mode",choices=("run","replay"))
    cli.add_argument("directory",type=Path)
    cli.add_argument("--model",type=Path)
    args=cli.parse_args()
    with configured():
        if args.mode=="run":
            if args.model is None:
                cli.error("--model is required")
            with patch.object(base.runner,"episode",new=base.episode), patch.object(base.runner,"locks",new=locks):
                base.runner.run(args.model,args.directory)
        else:
            print(json.dumps(base.replay(args.directory),indent=2))
