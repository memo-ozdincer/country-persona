"""Estimate how much a permissive reading of the two matched clauses could change."""
from copy import deepcopy
import json
from unittest.mock import patch

import focused


def run():
    marks=deepcopy(focused.read(focused.HERE/"marks.json"))
    marks["malta/authority"]["status"]="supported"
    marks["a3plus/review"]["status"]="relation"
    read=focused.read

    def replace(path):
        return marks if path==focused.HERE/"marks.json" else read(path)

    with patch.object(focused,"read",side_effect=replace):
        scores=focused.act("score")
    return {"changes":{"malta/authority":"supported, relation still omitted","a3plus/review":"relation accepted"},
            "policy":{k:v["summary"] for k,v in scores["policy"].items()}}


if __name__=="__main__":
    print(json.dumps(run(),indent=2))
