"""Exercise the frozen benchmark contract and reject common invalid submissions."""
from itertools import product
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory

import evaluate as e
import report
from run_suite import verify_release

FULL = (
    "On 27 June 2018 the Council adopted Peru’s draft S/2018/628 as Resolution 2422, 14–0–1 "
    "with Russia abstaining. Under Chapter VII it appointed Serge Brammertz Mechanism Prosecutor "
    "from 1 July 2018 until 30 June 2020, concluded its progress review and underlined full state cooperation. "
    "Peru called for Council unity and said combating impunity required states to enforce sentences, "
    "execute warrants and answer assistance requests. Russia linked its abstention to earlier staffing "
    "concerns and criticized administration. It questioned Mladić’s care and recalled requesting temporary "
    "release to Russia for treatment under Russian guarantees if prison doctors could not provide it. "
    "Serbia, participating without a vote, objected that the Mechanism refused temporary medical release "
    "despite Serbian guarantees. Serbia said it met its cooperation obligations and would prosecute war "
    "crimes regardless of nationality."
)
SOURCE = {
    "disposition": "vote", "capacity": "vote", "action": "action", "review": "action",
    "per-cooperation": "per-cooperation", "per-unity": "per-unity", "rus-staffing": "rus-staffing",
    "rus-medical": "rus-medical", "srb-release": "srb-release", "srb-cooperation": "srb-cooperation",
    "contrast": "per-unity",
}


def reject(fn):
    try:
        fn()
    except ValueError:
        return
    raise AssertionError("Invalid submission was accepted")


def sample(case, arm, order, answer):
    submitted = []
    calls = []
    for step in range(3):
        row = e.build_request(case, arm, order, calls)
        payload = json.loads(row["messages"][-1]["content"])
        assert "rubric" not in payload and "gold" not in payload
        if step < 2 and arm != "solo":
            desk = order if step == 0 else 1 - order
            assert not set(row["source_ids"]) & {b["id"] for b in case["owned"][1 - desk]}
        if step == 1 and arm == "independent":
            assert not row["visible"] and not payload["notes"]
        text = answer if step == 2 else payload["source_blocks"][-1]["text"]
        submitted.append({"request_sha256": e.checksum(row), "text": text, "input_tokens": 30,
                          "output_tokens": 10, "termination": "complete"})
        calls = e.validate_calls(case, arm, order, submitted)
    return submitted, calls


def verdicts(case, calls, full=False):
    f = e.final_packet(case, calls)
    supported = e.judge.by_id(f["evidence"])
    units = []
    for rule in f["rubric"]:
        if full:
            blocks = [SOURCE[rule["id"]]]
            if rule["id"] == "capacity":
                blocks.append("srb-release")
            if rule["id"] == "contrast":
                blocks.append("rus-staffing")
            source = [{"block": key, "quote": supported[key]["text"]} for key in blocks]
        else:
            source = []
        units.append({"id": rule["id"], "source": source, "response": f["answer"] if full else "",
                      "status": "met" if full else "unmet",
                      "reason": "Reviewed Resolution 2422 reference." if full else "Synthetic missing-coverage control."})
    final = {"id": f["id"], "units": units,
             "guard": {"status": "clear", "source": [], "response": "", "reason": "Fixture contains no fabrication."}}
    p = e.process_packet(case, calls)
    process = {"id": p["id"], "ideas": [],
               "ratings": [{"id": item, "points": 0, "spans": [], "source": [], "reason": "Zero-grade fixture."}
                           for group in e.PROCESS.values() for item in group]}
    return final, process


def adapter():
    for line in sys.stdin:
        request = json.loads(line)
        data = json.loads(request["messages"][-1]["content"])
        if "rubric" in data:
            text = json.dumps({"id": data["id"], "units": [
                {"id": r["id"], "status": "unmet", "source": [], "response": "", "reason": "Fixture omits this."}
                for r in data["rubric"]],
                "guard": {"status": "clear", "source": [], "response": "", "reason": "No claims in fixture."}})
        elif "dimensions" in data:
            text = json.dumps({"id": data["id"], "ratings": [
                {"id": k, "points": 0, "spans": [], "source": [], "reason": "No contributions in fixture."}
                for group in data["dimensions"].values() for k in group], "ideas": []})
        else:
            text = "The available record is incomplete."
        print(json.dumps({"text": text, "input_tokens": 1, "output_tokens": 1, "termination": "complete"}), flush=True)


def check_adapter():
    with TemporaryDirectory() as folder:
        path = Path(folder)
        config = path / "adapter.json"
        actor, judge = path / "actor", path / "judge"
        config.write_text(json.dumps({
            "model": "deterministic software fixture",
            "command": [sys.executable, str(Path(__file__).resolve()), "--adapter"],
        }))
        command = [sys.executable, str(e.HERE / "run_suite.py")]
        subprocess.run([*command, "collect", config, actor], check=True)
        subprocess.run([*command, "judge", config, judge, "--input", actor / "episodes.jsonl"], check=True)
        calls = [json.loads(line) for line in (actor / "actors.jsonl").read_text().splitlines()]
        counts = {"logical_actor_calls": len(calls), "physical_actor_calls": sum(not r["reused"] for r in calls),
                  "judge_calls": len((judge / "judges.jsonl").read_text().splitlines()),
                  "scored": e.read(judge / "comparison.json")["scored"]}
        assert counts == {"logical_actor_calls": 126, "physical_actor_calls": 112, "judge_calls": 84, "scored": 42}
        return counts


def run():
    verify_release()
    cases = e.cases()
    assert len(cases) == 7 and len({row["family"] for row in cases.values()}) == 5
    sample_paths = []
    failures = 0
    for case, arm, order in product(cases.values(), e.ARMS, (0, 1)):
        e.judge.by_id(e.evidence(case))
        assert sum(r["weight"] for r in case["rubric"]) == 70
        assert (e.HERE / case["reference"]).is_file()
        full = case["id"] == "tribunals"
        if case["track"] == "workshop":
            options = case["options"]
            match = [p["id"] for p in options if all(
                p[field] == value for condition in case["membership"] for field, value in condition.items())]
            assert (match or ["IMPASSE"]) == case["gold"]
            answer = f'Decision: {case["gold"][0]}'
        else:
            answer = FULL if full else "The available record is incomplete."
        inputs, calls = sample(case, arm, order, answer)
        final, process = verdicts(case, calls, full)
        result = e.final_score(case, calls, final)
        if full:
            assert result["released_70"] == 70 and result["strict"]
            saved = final["units"][0]["source"][0]["quote"]
            final["units"][0]["source"][0]["quote"] = "Invented source citation."
            reject(lambda: e.final_score(case, calls, final))
            final["units"][0]["source"][0]["quote"] = saved
            failures += 1
        elif case["track"] == "workshop":
            assert result["mechanical"]["accepted"]
            _, wrong = sample(case, arm, order, "Decision: UNRESOLVED")
            wrong_final, _ = verdicts(case, wrong)
            assert not e.final_score(case, wrong, wrong_final)["mechanical"]["accepted"]
        for row in calls:
            assert len(row["visible"]) <= 2
        sample_paths.append({"id": f"{case['id']}/{arm}/{order}", "calls": inputs, "final": final, "process": process})
    output = report.run(sample_paths)
    assert output["scored"] == 42 and all(
        all(unit["released_70"] >= 0 for unit in g["macro"].values()) for g in output["tracks"].values())
    reject(lambda: report.run(sample_paths[:-1]))
    reject(lambda: e.validate_calls(cases["tribunals"], "peer", 1, sample_paths[0]["calls"]))

    case = cases["tribunals"]
    _, calls = sample(case, "peer", 0, FULL)
    _, process = verdicts(case, calls)
    retained = next(r for r in process["ratings"] if r["id"] == "traceable_uptake_or_correction")
    retained["points"] = 5
    retained["spans"] = [{"turn": i, "quote": calls[i]["text"]} for i in (0, 1)]
    retained["source"] = [{"block": "per-unity", "quote": case["owned"][0][1]["text"]}]
    reject(lambda: e.process_score(case, calls, process))
    retained["spans"].append({"turn": 2, "quote": "Peru called for Council unity"})
    assert e.process_score(case, calls, process)["process_30"]["interactions"] == 5

    _, capped = sample(case, "peer", 0, FULL)
    capped[-1]["termination"] = "cap"
    marked, _ = verdicts(case, capped, full=True)
    assert e.final_score(case, capped, marked)["released_70"] == 0
    return {"cases": len(cases), "families": 5, "scored_software_fixtures": output["scored"],
            "workshop_decision_keys": 4, "fabricated_citation_rejections": failures,
            "negative_gates": ["missing paired run", "call hash from wrong condition",
                               "unresolved decision", "uncited final uptake", "truncated final"],
            "adapter_round_trip": check_adapter()}


if __name__ == "__main__":
    if sys.argv[1:] == ["--adapter"]:
        adapter()
    else:
        e.emit(run())
