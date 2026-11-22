"""Measure admission errors at actual and constructed certificate boundaries."""
import argparse
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))
from decision_ledger import readout

MALI = HERE.parents[1] / "mali"
BUNDLE = HERE.parent / "evidence/bundle-policy/mali.json"


def audit(metrics, factored=None):
    case = json.loads((MALI / "case.json").read_text())
    fixtures = {f["id"]: f for f in json.loads((HERE/"fixtures.json").read_text())}
    options = [p["id"] for p in case["options"]]
    archive = json.loads(BUNDLE.read_text())
    path_id = "reversed/france-overlap/bundle_first/CA"
    trace = archive["paths"][path_id]
    archived = next(c for c in trace["claims"] if c["id"] == "claim-3")
    assert archived == {"id":"claim-3","role":"FRANCE","accepts":["E"],"excludes":["C"]}
    contexts = {
        "M1": trace["claims"],
        "M2": trace["claims"],
        "M3": trace["claims"],
        "M4": [archived, {"id":"claim-4","role":"RUSSIAN FEDERATION","accepts":["E"],"excludes":[]}],
    }
    report = {}
    for ident, context in contexts.items():
        fixture = fixtures[ident]
        outcome = metrics["bundles"][ident]
        joint, split = (outcome["decoded"][arm] for arm in ("joint","split"))
        modes = {"authored":outcome["expected"],"joint":joint,"split":split,
                 "corroborated":[j is True and s is True for j,s in zip(joint,split,strict=True)]}
        if factored is not None:
            modes["factored"] = factored["bundles"][ident]["decoded"]["factored"]
        arms = {}
        for arm, signs in modes.items():
            replacement = {"id":"claim-3","role":fixture["role"],
                           "accepts":[fixture["accept"]] if signs[0] is True else [],
                           "excludes":[fixture["exclude"]] if signs[1] is True else []}
            claims = [replacement if claim["id"]=="claim-3" else claim for claim in context]
            state = readout(options,case["roles"],claims)
            arms[arm] = {"admitted":replacement,"decision":state}
        report[ident] = arms
    assert report["M1"]["authored"]["decision"] == trace["ledger"]
    assert report["M2"]["authored"]["decision"]["state"] == "AGREEMENT_POSSIBLE"
    assert report["M3"]["authored"]["decision"]["state"] == "UNRESOLVED"
    assert report["M4"]["authored"]["decision"]["state"] == "UNRESOLVED"
    return {"scope":"M1–M3 replace a single claim in a recorded path with its authored-language interpretation, holding later messages fixed. M4 is a constructed near-certificate guard. Protocol counterfactual only.",
            "case_path":path_id,"states":report}


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("metrics",type=Path)
    p.add_argument("--factored",type=Path)
    args = p.parse_args()
    additional = json.loads(args.factored.read_text()) if args.factored else None
    print(json.dumps(audit(json.loads(args.metrics.read_text()), additional),indent=2))
