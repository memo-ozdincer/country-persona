"""Add a source-checked consultation comparison to the reviewed Sudan memos."""
from hashlib import sha256
import json
from pathlib import Path
import sys

from source_route_fit import CASE

REQUIRED = ("RU-B", "CN-B")
UNKNOWN = "The received evidence does not establish a shared consultation position."
OVERLAP = (
    "Both delegations called for involving Sudanese authorities. Russia required central-authority agreement "
    "for humanitarian measures. China called for consultation with the Government and other relevant parties "
    "[RU-B, CN-B]."
)
LABEL = "\n\n**Analytical Next Step:**"


def conclusion(packet, authorized):
    for key, value in packet.items():
        if key not in authorized or authorized[key] != value:
            raise ValueError(f"Source {key} differs from the frozen dossier")
    return OVERLAP if all(key in packet for key in REQUIRED) else UNKNOWN


def compose(directory):
    path=directory/"transcript.jsonl"
    marks=json.loads((directory/"scores.json").read_text())
    annotations=json.loads((directory/"annotations.json").read_text())["reviews"]
    identity=sha256(path.read_bytes()).hexdigest()
    assert marks["transcript_sha256"]==identity
    case=json.loads(CASE.read_text())
    authorized={**case["docket"],**{k:v for portfolio in case["delegate_evidence"].values() for k,v in portfolio.items()}}
    assert "agreement with Sudan's central authorities" in authorized["RU-B"]
    assert "consultation with Sudan's Government and other relevant parties" in authorized["CN-B"]
    rows, rejected=[],[]
    for raw in map(json.loads,path.read_text().splitlines()):
        ident=raw["id"]
        score=marks["records"][ident]
        assert score["critical_guard"]=="clear" and not score["common_ground_realized"]
        visible=json.loads(raw["messages"][-1]["content"])["evidence"]
        assert list(visible)==raw["evidence_ids"]
        line=conclusion(visible,authorized)
        body=raw["output"]
        removed=None
        if not raw["ended"]:
            body, removed=body.rsplit(LABEL,1)
            assert body.endswith(".")
        result=line+"\n\n"+body
        covered=line==OVERLAP
        assert covered==score["common_ground_warrant"]
        assert len(result.split())<=160
        key=sha256(("source-route-memo/"+ident).encode()).hexdigest()[:10]
        passed={unit:desc[2] for unit,desc in annotations[key]["units"].items() if desc[0]=="met"}
        assert 7*len(passed)==score["floor"]
        dropped=[unit for unit,span in passed.items() if span not in body]
        assert not set(dropped)-{"S2"}
        rows.append({"id":ident,"received_sources":list(visible),"comparison":line,
                     "common_ground_supported":covered,
                     "retained_model_text":body,"withheld_last_section":removed,
                     "record":result,"words":len(result.split()),
                     "new_validated_criterion_points":7*covered,
                     "dropped_credited_units":dropped,
                     "carried_forward_plus_compiled_points":score["floor"]+7*covered-7*len(dropped)})
        for name, variation in (
            ("unknown_source", {**visible,"FAKE":"Fabricated qualification"}),
            ("changed_source", {**visible,"TEXT":authorized["TEXT"]+" Changed policy."}),
        ):
            try:
                conclusion(variation,authorized)
            except ValueError:
                rejected.append({"id":ident,"mutation":name})
            else:
                raise AssertionError("Unverified source accepted")
    assert len(rows)==4 and sum(r["common_ground_supported"] for r in rows)==1
    return {"scope":"Post-test same-case composition from frozen source IDs and reviewed original writer text. The factual body is used as archived, except that an unfinished ending section is withheld. The consultation sentence is explicitly authored and proof-gated.",
            "raw_sha256":identity,"case_sha256":sha256(CASE.read_bytes()).hexdigest(),
            "records":rows,"rejected_source_mutations":rejected}


if __name__=="__main__":
    print(json.dumps(compose(Path(sys.argv[1])),indent=2,ensure_ascii=False))
