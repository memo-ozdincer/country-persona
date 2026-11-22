"""Count criteria whose necessary evidence is reachable through one source per desk."""
from itertools import product
import json

import exact_notes as run

# These source dependencies describe evidence availability only. They do
# not grade model outputs or claim the writer will assemble the record.
NEEDED = {
    "myanmar": {
        "draft-act":["vote"],"vote-count":["vote"],"uk":["vote","uk"],"india":["india"],
        "role":["chair","india"],"humanitarian":["mandate"],"asean":["mandate"],
        "overlap":["vote","uk","india"],"reporting":["mandate"],"authority":["vote","chair"],
    },
    "tribunals": {
        "disposition":["vote"],"capacity":["vote","srb-release"],"action":["action"],"review":["action"],
        "per-cooperation":["per-cooperation"],"per-unity":["per-unity"],"rus-staffing":["rus-staffing"],
        "rus-medical":["rus-medical"],"srb-release":["srb-release"],"srb-cooperation":["srb-cooperation"],
        "contrast":["per-unity","rus-staffing"],
    },
}


def available():
    out={}
    for key, dependencies in NEEDED.items():
        case=run.e.cases()[key]
        weights={r["id"]:r["weight"] for r in case["rubric"]}
        assert weights.keys()==dependencies.keys()
        public={b["id"] for b in case["public"]}
        rows=[]
        for a,b in product(*[[r["id"] for r in blocks] for blocks in case["owned"]]):
            visible=public|{a,b}
            covered=[name for name,sources in dependencies.items() if set(sources)<=visible]
            rows.append({"source_ids":[a,b],"potential_points":sum(weights[name] for name in covered),
                         "supported_criteria":covered})
        out[key]={"cases":rows,"best":max(row["potential_points"] for row in rows)}
    return out


if __name__=="__main__":
    print(json.dumps(available(),indent=2))
