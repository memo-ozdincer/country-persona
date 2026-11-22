"""Attribute clearance changes to the named subchecks."""
from itertools import combinations
import json

import scoped


def audit():
    evaluated=scoped.e.read(scoped.HERE/"results.json")["results"]
    reports={}
    for cohort,rows in evaluated.items():
        summary={}
        for size in range(1,len(scoped.DOMAINS)+1):
            for names in combinations(scoped.DOMAINS,size):
                outgoing={}
                for key,row in rows.items():
                    passed=all(row["checks"][domain]["verdict"]=="clear" for domain in names)
                    outgoing[key]=(passed,row["target"]=="clear")
                summary["+".join(names)]={
                    "clears":sum(outcomes[0] for outcomes in outgoing.values()),
                    "false_clear":[key for key,(passed,true) in outgoing.items() if passed and not true],
                    "false_block":[key for key,(passed,true) in outgoing.items() if true and not passed],
                }
        unanimous={
            key:(all(check["orders"]==["clear","clear"] for check in row["checks"].values()),
                 row["target"]=="clear")
            for key,row in rows.items()
        }
        report={"combination":summary,"all_six_labels_clear":{
            "clears":sum(passed for passed,_ in unanimous.values()),
            "false_clear":[key for key,(passed,true) in unanimous.items() if passed and not true],
            "false_block":[key for key,(passed,true) in unanimous.items() if true and not passed],
        },"false_clears_from_previous_guard":{
            key:[domain for domain,val in row["checks"].items() if val["verdict"]!="clear"]
            for key,row in rows.items() if row["previous"]=="clear" and row["target"]!="clear"
        }}
        reports[cohort]=report
    return reports


if __name__=="__main__":
    print(json.dumps(audit(),indent=2))
