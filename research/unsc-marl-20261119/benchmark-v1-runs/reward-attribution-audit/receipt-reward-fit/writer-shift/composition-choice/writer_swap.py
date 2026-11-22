"""Reevaluate the frozen draft-choice policy with different archived writers."""
import json

import numpy as np

import compose_choice as c


def run():
    original=c.HERE/"results.json"
    receipts=c.reform()
    layout=receipts["layout"]
    inputs={
        "original_free_form":c.REFORM/"scores.json",
        "authority_clarification":c.REFORM/"authority-clarification/scores.json",
        "split_lead":c.REFORM/"public-record-anchor/scores.json",
    }
    readout=c.read(original)["dockets"]["2553"]["budgets"]["256"]["admission_rates"]
    # Receipt-level means are sufficient for expected linear scores.
    usage=np.array([readout[k] for k in receipts["ids"]])
    baseline=receipts["verbatim"]
    output={}
    for name,path in inputs.items():
        grades=c.read(path)["grades"]
        assert set(grades)==set(receipts["ids"])
        rewrite=np.asarray([grades[id_]["released_70"] for id_ in receipts["ids"]])
        by_editor={}
        for editor,mass in layout(.75,.75).items():
            released=float((baseline+(rewrite-baseline)*usage)@mass)
            native_use=float(usage@mass)
            by_editor[editor]={"release":released,"native_use":native_use,
                               "verbatim":float(baseline@mass),"net":released-c.FEE*native_use}
        output[name]=by_editor
    rows=c.read(original)["dockets"]["2553"]["budgets"]["256"]["evaluation"]
    for row in rows:
        if (row["q"],row["prior"])==(.75,.75):
            assert abs(output["split_lead"][row["editor"]]["net"]-row["outcomes"]["fit"]["net"])<1e-9
    return {"frozen_policy_sha256":c.pin(original),"input_sha256":{k:c.pin(p) for k,p in inputs.items()},
            "held_writer_replay":output}


if __name__=="__main__":
    print(json.dumps(run(),indent=2))
