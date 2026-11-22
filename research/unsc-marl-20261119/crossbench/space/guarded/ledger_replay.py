"""Check explicit sender-owned submissions at recorded agreement boundaries."""
import json
from pathlib import Path
import sys

from admit import submit

HERE = Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[1]))
from decision_ledger import readout


def read(path):
    return json.loads(path.read_text())


def evaluate():
    base = HERE.parent
    mali = HERE.parents[1]/"mali"
    parts = {
        "mali": read(mali/"evidence/metrics.json")["package_predictions"],
        "space": read(base/"evidence/metrics.json")["decisions"],
    }

    def receipt(case, card, role, choices):
        signs = parts[case][card] if case=="mali" else {
            k:parts[case][f"{card}/{k}"] for k in choices
        }
        return {"role":role,"accepts":[k for k in choices if signs[k]["sign"] is True],
                "excludes":[k for k in choices if signs[k]["sign"] is False]}

    def envelope(id_, role, yes, no):
        return {"id":id_,"role":role,"accepts":yes,"excludes":no}

    original = read(base/"evidence/bundle-policy/mali.json")["paths"]["reversed/france-overlap/bundle_first/CA"]
    focus = next(c for c in original["claims"] if c["id"]=="claim-3")
    verified = receipt("mali","france-overlap","FRANCE","ABCDEFG")
    uncertain = {**verified,"excludes":[k for k in verified["excludes"] if k!="C"]}
    output = {}
    for name,ticket,atomic in (
        ("true_bundle",verified,False),
        ("one_missing_selective",uncertain,False),
        ("one_missing_atomic",uncertain,True),
    ):
        signed,audit = submit(focus,actor="FRANCE",receipt=ticket,labels="ABCDEFG",atomic=atomic)
        messages = [signed if c["id"]==focus["id"] else c for c in original["claims"]]
        ledger = readout("ABCDEFG",("FRANCE","RUSSIAN FEDERATION"),messages)
        output[name] = {"admitted":signed,"receipt":audit,"state":ledger["state"]}
    wrong = envelope("claim-3","FRANCE",["E"],["A"])
    proof = receipt("mali","france-impasse","FRANCE","ABCDEFG")
    accepted,audit = submit(wrong,actor="FRANCE",receipt=proof,labels="ABCDEFG")
    peer = envelope("claim-4","RUSSIAN FEDERATION",["E"],[])
    state = readout("ABCDEFG",("FRANCE","RUSSIAN FEDERATION"),[accepted,peer])["state"]
    output["mandate_foil"] = {"admitted":accepted,"receipt":audit,"state":state}
    peer = envelope("peer","JAPAN",["F"],[])
    verified = receipt("space","china-overlap","CHINA","ABCDEFG")
    false = envelope("parser","CHINA",["F"],[])
    tasks = (
        ("question_has_no_signed_event",[]),
        ("parser_claims_owner_binding",[submit(false,actor="CHINA",receipt=verified,labels="ABCDEFG")[0]]),
    )
    for name,claims in tasks:
        state = readout("ABCDEFG",("CHINA","JAPAN"),[peer,*claims])["state"]
        output[name] = {"state":state}
    assert {k:v["state"] for k,v in output.items()} == {
        "true_bundle":"AGREEMENT_POSSIBLE",
        "one_missing_selective":"AGREEMENT_POSSIBLE",
        "one_missing_atomic":"UNRESOLVED",
        "mandate_foil":"UNRESOLVED",
        "question_has_no_signed_event":"UNRESOLVED",
        "parser_claims_owner_binding":"AGREEMENT_POSSIBLE",
    }
    return {"scope":"Recorded and constructed boundaries. Owner binding is supplied by the trusted scheduler. The last control deliberately violates that boundary.",
            "outcomes":output}


if __name__=="__main__":
    print(json.dumps(evaluate(),indent=2))
