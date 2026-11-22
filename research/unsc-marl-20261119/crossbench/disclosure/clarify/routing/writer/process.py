"""Measure decision-relevant disclosures in the two matched sanctions runs."""
from collections import Counter, defaultdict
import json
import sys

from run import ROOT

sys.path.insert(0, str(ROOT.parents[2]))
from decision_ledger import readout


def summarize():
    dossier = json.loads((ROOT/"sanctions.json").read_text())
    evidence = json.loads((ROOT/"evidence/sanctions.json").read_text())
    roles = dossier["roles"]
    packages = [item["id"] for item in dossier["options"]]
    rows = {}
    for replay in evidence["replays"]:
        variant, opening, arm = replay["variant"], "".join(replay["opening"]), replay["arm"]
        if variant!="impasse" or opening not in ("AC","BC"):
            continue
        claims = replay["public_claims"]
        inventory = defaultdict(set)
        counts = Counter()
        for item in claims:
            for sign in ("accepts","excludes"):
                for option in item[sign]:
                    inventory[item["role"]].add((sign,option))
                    counts[sign] += 1
        first = next((len_ - 2 for len_ in range(2,len(claims)+1)
                      if readout(packages,roles,claims[:len_])["state"]!="UNRESOLVED"),None)
        assert replay["continuation_slots"]==len(claims)-2
        rows[f"{opening}/{arm}"] = {"turns":len(claims), "signed_claims":dict(counts),
                                   "unique_by_delegate":{role:len(inventory[role]) for role in roles},
                                   "first_certificate_continuation":first,
                                   "missing":replay["readout"]["unresolved_options"]}
    return rows


if __name__=="__main__":
    print(json.dumps(summarize(),indent=2))
