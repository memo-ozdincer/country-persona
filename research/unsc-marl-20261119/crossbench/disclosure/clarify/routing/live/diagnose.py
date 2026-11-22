"""Compare saved role replies with the exact-field oracle on identical episodes."""
import argparse
from collections import Counter
import json
from pathlib import Path

from episode import episode,serialize


def diagnose(root):
    observed = list(map(json.loads,(root/"transcript.jsonl").read_text().splitlines()))
    signs = Counter()
    failures = []
    for row in observed:
        body = json.loads(row["messages"][1]["content"])
        local = body["local_comparison"]
        expected = "accept" if local["private_requirements"]==local["package_values"] else "exclude"
        try:
            answer = json.loads(row["output"])
            actual = answer.get("stance","malformed") if isinstance(answer,dict) else "malformed"
        except ValueError:
            actual = "malformed"
        signs[f"{expected}/{actual}"] += 1
        if expected!=actual:
            failures.append({"id":row["id"],"role":body["delegate"],"option":local["option"],
                             "expected":expected,"observed":actual,
                             "visible_claims":len(body["public_disclosures"])})

    def oracle(batch):
        out = {}
        for row in batch:
            local = json.loads(row["messages"][1]["content"])["local_comparison"]
            sign = "accept" if local["private_requirements"]==local["package_values"] else "exclude"
            out[row["id"]] = {"output":serialize({"option":local["option"],"stance":sign})}
        return out

    exact = episode(oracle)
    actual = json.loads((root/"metrics.json").read_text())
    outcomes = {}
    for key, row in actual["episodes"].items():
        control = exact["episodes"][key]
        outcomes[key] = {"actual":row["readout"]["state"],"truthful_reply_control":control["readout"]["state"],
                         "actual_admitted":row["admissions"].get("admitted",0),
                         "actual_attempts":len(row["attempts"])}
    return {"unique_signs":dict(signs),"sign_failures":failures,"outcomes":outcomes,
            "truthful_control_unique_requests":exact["records"]}


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("run",type=Path)
    print(json.dumps(diagnose(p.parse_args().run),indent=2))
