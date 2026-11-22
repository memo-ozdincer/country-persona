"""Create and run frozen source-claim probes on the two transfer dockets."""
import argparse
import json
from pathlib import Path
import sys
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
RUNS = HERE.parent
PREVIOUS = RUNS / "role-scoped-comparison"
TRAIN = RUNS / "paired-sender-credit"
REF = RUNS / "relation-support-transfer" / "scores.json"
CASE_2664 = RUNS / "humanitarian-2664-admission/case.json"
CASE_2739 = RUNS / "reporting-2739/docket.json"
sys.path.insert(0, str(PREVIOUS))
import collect_cpu as cpu
import collect_roles as prior

collector = prior.collector
read = prior.read


def fixtures():
    c2664, c2739 = map(read, (CASE_2664, CASE_2739))
    archives = read(REF)["deployment"]
    output = {}
    private_2664 = {b["id"]: b["text"] for b in c2664["evidence"]}
    private_2739 = {b["id"]: b["text"] for desk in c2739["owned"] for b in desk}
    case_blocks_2664 = archives["2664"]["fixed_record"].split(". ")
    case_blocks_2739 = archives["2739"]["fixed_record"].split(". ")
    assert len(case_blocks_2664) == 5 and len(case_blocks_2739) == 6

    def sentence(parts, i):
        return parts[i].rstrip(".") + "."

    for key, row in {
        "2664": {
            "rubric": c2664["rubric"], "cap": c2664["word_cap"],
            "public": {"vote": sentence(case_blocks_2664, 0), "scope": sentence(case_blocks_2664, 1)},
            "early": {
                "full": (private_2664["india"], {"india": sentence(case_blocks_2664, 4)}),
                "diversion": ("Speaking for India, the representative warned of diversion under the ISIL and Al-Qaida regime.",
                              {None: "India warned of diversion under the ISIL and Al-Qaida regime."}),
                "request-only": ("India had sought proactive involvement by the 1267 Monitoring Team and robust reporting standards and mechanisms.",
                                 {None: "India had sought proactive Monitoring Team involvement and robust reporting."}),
            },
            "late": {
                "standalone": (sentence(case_blocks_2664, 2), {"term": sentence(case_blocks_2664, 2)}),
                "relational": (private_2664["safeguards"].split(". ", 1)[1],
                               {"safeguards": sentence(case_blocks_2664, 3)}),
            },
            "early_claim": "India says the adopted text did not fully address its request for proactive Monitoring Team involvement or robust reporting.",
            "late_claim": "The adopted text establishes monitoring by the 1267 Committee or another specified sanctions oversight or reporting channel.",
            "relation": "relation",
        },
        "2739": {
            "rubric": c2739["rubric"], "cap": c2739["word_cap"],
            "public": {"disposition": sentence(case_blocks_2739, 1), "draft-and-sponsors": sentence(case_blocks_2739, 0),
                       "authority": "The adopted text conferred no new authorization of military action."},
            "early": {
                "full": (private_2739["algeria"],
                         {"algeria-reason": sentence(case_blocks_2739, 4)+" "+sentence(case_blocks_2739, 5)}),
                "objection": (private_2739["algeria"].split(". ")[-1], {"algeria-reason": sentence(case_blocks_2739, 5)}),
                "voted-only": (private_2739["algeria"].split(". ")[0]+".", {None: "Algeria abstained."}),
            },
            "late": {
                "standalone": ("Operative paragraph 1 extended the Secretary-General’s reporting request under paragraph 10 of resolution 2722 (2024) until 15 January 2025.",
                               {"operative-report": sentence(case_blocks_2739, 2).split(", without")[0]+"."}),
                "relational": (private_2739["sponsors"], {"sponsor-reason": sentence(case_blocks_2739, 3)}),
            },
            "early_claim": "Algeria says continued reporting on attacks keeps the Council informed and separately gives an implementation or self-defence concern as its reason for abstaining.",
            "late_claim": "The co-sponsors explicitly say that continuing the Secretary-General's reporting on the attacks gives the Council information useful for future deliberations.",
            "relation": "bounded-overlap",
        },
    }.items():
        # An unweighted source passage can still be included in the final record.
        # Keep its key textual through plan serialization.
        for side in ("early", "late"):
            row[side] = {label: {"text": text, "record": {str(k): v for k, v in brief.items()}}
                         for label, (text, brief) in row[side].items()}
        output[key] = row | {"clause": archives[key]["candidate"]}
    return output


def plan():
    cases = fixtures()
    requests = []
    for docket, case in cases.items():
        for side in ("early", "late"):
            for key, card in case[side].items():
                for order, mapping in prior.prior.MAPPINGS.items():
                    payload = {"source_role": "delegate_statement" if side == "early" else "document_desk_evidence",
                               "source_text": card["text"], "proposition": case[f"{side}_claim"],
                               "responses": {label: "established" if meaning == "process" else "not established"
                                             for label, meaning in mapping.items()}}
                    requests.append(prior.prior.base.earlier.request(f"{docket}/{side}/{key}/{order}", 2,
                                                                    prior.SYSTEM, payload))
    assert len(requests) == 20
    files = (Path(__file__), HERE / "fit.py", HERE / "protocol.md", REF, CASE_2664, CASE_2739,
             PREVIOUS / "collect_roles.py", PREVIOUS / "collect_cpu.py",
             TRAIN / "experiment.py", TRAIN / "value_sender.py", TRAIN / "value-plan.json")
    return {"cases": cases, "requests": requests, "checkpoint_index_sha256":
            collector.sha(collector.MODEL / "model.safetensors.index.json"),
            "pins": {str(p.relative_to(RUNS.parent)): collector.sha(p) for p in files}}


def serial():
    return json.loads(json.dumps(plan(), ensure_ascii=False))


def act(mode):
    data = serial()
    if mode == "plan":
        return data
    assert data == read(HERE / "plan.json")
    with patch.object(cpu, "HERE", HERE), patch.object(cpu, "OUT", HERE / "evidence-cpu"), patch.object(
            cpu, "locked", return_value=data):
        return {"run": cpu.run, "verify": cpu.verify}[mode]()


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode", choices=("plan", "run", "verify"))
    m = p.parse_args().mode
    out = act(m)
    if m != "run":
        print(json.dumps(out, ensure_ascii=False, indent=2))
