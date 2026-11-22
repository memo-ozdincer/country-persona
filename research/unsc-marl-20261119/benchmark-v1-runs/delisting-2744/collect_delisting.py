"""Collect source-claim logits on the locked delisting dossier."""
import argparse
import json
from pathlib import Path
import sys
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
RUNS = HERE.parent
ROLE = RUNS / "role-scoped-comparison"
BRIDGE = RUNS / "value-routing-docket-transfer"
TRAIN = RUNS / "paired-sender-credit"
sys.path.insert(0, str(ROLE))
import collect_roles as prior
import collect_cpu as cpu

read = prior.read
collector = prior.collector


def plan():
    case = read(HERE / "case.json")
    requests = []
    for side in ("early", "late"):
        cards = {key: (card["text"], list(case["relations"])) for key, card in case[side].items()}
        cards |= {key: (row["text"], [row["type"]]) for key, row in case["controls"].items()
                  if row["side"] == side}
        for key, (text, types) in cards.items():
            for relation in types:
                for order, mapping in prior.prior.MAPPINGS.items():
                    payload = {"source_role": "delegate_statement" if side == "early" else "adopted_provision",
                               "source_text": text, "proposition": case["relations"][relation][side+"_claim"],
                               "responses": {letter: "established" if value=="process" else "not established"
                                             for letter, value in mapping.items()}}
                    requests.append(prior.prior.base.earlier.request(f"{side}/{key}/{relation}/{order}",
                                                                    2, prior.SYSTEM, payload))
    assert len(requests) == 28
    files = (Path(__file__), HERE/"case.json", HERE/"protocol.md", HERE/"fit_delisting.py",
             BRIDGE/"fit.py", BRIDGE/"plan.json", BRIDGE/"verified.json",
             TRAIN/"value_sender.py", TRAIN/"experiment.py", ROLE/"collect_roles.py", ROLE/"collect_cpu.py")
    return {"case":case,"requests":requests,"checkpoint_index_sha256":
            collector.sha(collector.MODEL/"model.safetensors.index.json"),
            "pins":{str(f.relative_to(RUNS.parent)):collector.sha(f) for f in files}}


def act(mode):
    data = plan()
    if mode == "plan":
        return data
    assert data == read(HERE/"plan.json")
    with patch.object(cpu,"HERE",HERE),patch.object(cpu,"OUT",HERE/"evidence-cpu"),patch.object(
            cpu,"locked",return_value=data):
        return {"run":cpu.run,"verify":cpu.verify}[mode]()


if __name__ == "__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode",choices=("plan","run","verify"))
    args=p.parse_args()
    result=act(args.mode)
    if args.mode!="run":
        print(json.dumps(result,ensure_ascii=False,indent=2))
