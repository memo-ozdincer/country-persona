"""Score the facilitator's disposition by class and across evidence interventions."""
import argparse
from collections import defaultdict
import json
from pathlib import Path

from common_ground import generate


def grade(predictions):
    pack=generate()
    by_id={r["id"]:r for r in predictions}
    if len(by_id)!=len(predictions) or set(by_id)!={r["id"] for r in pack["keys"]}:
        raise ValueError("Provide one prediction per input id")
    strata=defaultdict(list)
    panels=defaultdict(list)
    for task,ref in zip(pack["inputs"],pack["keys"],strict=True):
        decision=by_id[task["id"]]["decision"]
        if decision not in {"retain","revise","withhold"}:
            raise ValueError(f"Unknown disposition {decision!r}")
        hit=decision==ref["decision"]
        strata[ref["decision"]].append(hit)
        panels[task["docket"],task["proposed_sentence"]].append(hit)
    return {"by_required_action":{k:{"correct":sum(v),"total":len(v)} for k,v in strata.items()},
            "all_four_views_correct":sum(all(v) for v in panels.values()),
            "distinct_proposed_sentences":len(panels)}


if __name__=="__main__":
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument("predictions",type=Path)
    print(json.dumps(grade(json.loads(cli.parse_args().predictions.read_text())),indent=2))
