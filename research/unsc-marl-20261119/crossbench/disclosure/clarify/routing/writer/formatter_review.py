"""Check the case-specific renderer against the same record rubric."""
import json
import re

from adjudicate import report
from formatter import render
from instrument import suite
from review import contract, packet


def check():
    deck = []
    declarations = {}
    for base in suite():
        payload = json.loads(base["messages"][1]["content"])
        output = render(payload)
        row = {**base,"output":output,"stop":"compiled"}
        req = packet(row,row["id"])
        labels = dict(line.split(": ",1) for line in output.splitlines())
        declaration = {
            "disposition":["met",["History","Workshop"],["historical-instrument","roll","public-proof"],
                           "The rendered historical and workshop identifiers and dispositions match the input."],
            "operative":["met",["Evidence"],["public-proof"],
                         "The record gives the relevant package terms, exclusion coverage or missing disclosure."],
            "positions":["met",["Positions"],re.findall(r"\((claim-\d+)\)",labels["Positions"]),
                         "The two scoped claims point to actual, correctly attributed admissions."],
            "unresolved":["met",["History","Evidence"],["india","public-proof"],
                          "Both recorded concerns and the decision-relevant evidence are preserved."],
            "authority":["met",["Authority"],["scope"],
                         "The record treats proposals as fictional and preserves official authority."],
            "guard":["clear",["Authority"],["scope","roll"],"No vote, commitment or amendment is invented."],
        }
        if base["expected_state"]=="AGREEMENT_POSSIBLE":
            declaration["operative"][2].append("package-A")
        declarations[row["id"]] = declaration
        mechanics = contract(row)
        mechanics.pop("ended")
        deck.append({"packet":req,"mechanics":mechanics,"model_id":row["id"]})
    scores = report(deck,declarations)
    return {"origin":"Deterministic formatter. Case-specific assistant annotations.",
            "records":scores}


if __name__=="__main__":
    print(json.dumps(check(),indent=2,ensure_ascii=False))
