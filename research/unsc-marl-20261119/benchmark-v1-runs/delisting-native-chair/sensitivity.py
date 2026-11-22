"""Check whether disposition leniency or repaired standalone facts changes the result."""
import json
from unittest.mock import patch

import numpy as np

from replay import BASE, HERE, analyze, previous, read, team


def run():
    results = read(HERE/"results.json")
    scores = results["scores"]
    reference = read(BASE/"results.json")
    case = read(BASE/"case.json")
    weights = [tuple(np.array(reference[history][-1][param]) for param in ("sender","receiver"))
               for history in ("history","sampled_history")]
    native = previous["bank"](case,read(BASE/"verified.json")["outputs"])[1]
    variants={}
    for name in ("lenient_vote","fixed_standalone_keep_native_relation"):
        table = [arr.copy() for arr in native]

        def points(early,late):
            grade = scores[f"{early}/{late}"]
            if name == "lenient_vote":
                assert "vote" not in grade["met"]
                return grade["released"] + (14 if not grade["blockers"] else 0)
            return (30 + (case["early"][early]["weight"] if early is not None else 0)
                    + (case["late"][late]["weight"] if late is not None else 0)
                    + (18 if "relation" in grade["met"] and not grade["blockers"] else 0))

        table[0][1] = points(None,None)
        for v,early in enumerate(case["early"]):
            table[1][1,v] = points(early,None)
            for j,late in enumerate(case["late"]):
                table[2][1,j] = points(None,late)
                table[3][1,v,j] = points(early,late)
        with patch.object(team,"PRIVATE",{"2664":("full","diversion","request-only"),"2744":tuple(case["early"])}):
            report=analyze(table,*weights)
        variants[name]=report["mean_utility"]["2744"]
    return variants


if __name__=="__main__":
    print(json.dumps(run(),indent=2))
