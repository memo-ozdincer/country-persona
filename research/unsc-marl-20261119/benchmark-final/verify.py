"""Exercise the frozen benchmark contract and reject common invalid submissions."""
from itertools import product
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory

import evaluate as e
import report
import review
import calibrate
import action_contrasts
import information
from replay import run as replay_syria
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
                  "logical_judge_verdicts": len((judge / "judges.jsonl").read_text().splitlines()),
                  "scored": e.read(judge / "comparison.json")["scored"]}
        assert counts == {"logical_actor_calls": 126, "physical_actor_calls": 112, "logical_judge_verdicts": 84, "scored": 42}
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
        assert len(case["roles"]) == len(set(case["roles"])) == len(case["owned"]) == 2
        assert all((block.get("source") or block.get("url", "")).startswith("https://")
                   for block in e.evidence(case)
                   if block["id"] not in {"menu", "scope", "mandate-1", "mandate-2"})
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
            wrong_score = e.final_score(case, wrong, wrong_final)
            assert not wrong_score["mechanical"]["accepted"] and not wrong_score["release"]
            assert wrong_score["released_70"] == 0
            _, duplicate = sample(case, arm, order, answer + "\ndecision : UNRESOLVED")
            duplicate_final, _ = verdicts(case, duplicate)
            denied = e.final_score(case, duplicate, duplicate_final)
            assert denied["released_70"] == 0 and "invalid_decision_line" in denied["release_blockers"]
        for row in calls:
            assert len(row["visible"]) <= 2
        sample_paths.append({"id": f"{case['id']}/{arm}/{order}", "calls": inputs, "final": final, "process": process})
    output = report.run(sample_paths)
    marks = review.extract(sample_paths)
    queue, _ = review.packets(sample_paths)
    assert all(set(items) == set(marks[mode]) for mode, items in queue.items())
    assert all("calls" not in packet and "turns" not in packet for packet in queue["final"].values())
    assert report.run(review.combine(sample_paths, marks)) == output
    agreement = review.compare(sample_paths, marks, marks)
    assert all(row["total"] == row["agreed"] > 0 for row in agreement["counts"].values())
    final_id = sample_paths[0]["final"]["id"]
    altered = e.json.loads(e.json.dumps(marks))
    altered["final"][final_id]["units"][0]["status"] = "uncertain"
    assert review.compare(sample_paths, marks, altered)["disagreements"][0]["kind"] == "criterion"
    reject(lambda: review.combine(sample_paths, {"final": marks["final"], "process": {}}))
    assert len(calibrate.anchors()) == 10
    for packet, expect in calibrate.anchors().values():
        assert set(expect) <= {"guard"} | {r["id"] for r in packet["rubric"]}
    process_anchors = calibrate.process_anchors()
    assert len(process_anchors) == 4
    process_marks = {}
    for packet, expected, case, calls in process_anchors.values():
        _, marks = verdicts(case, calls)
        assert set(expected) <= {r["id"] for r in marks["ratings"]}
        assert packet["id"] == marks["id"]
        cited_block = next(block for block in packet["source_blocks"] if block["id"] == "status-639")
        for rating in marks["ratings"]:
            points = expected.get(rating["id"], 0)
            if points:
                indices = range(3) if rating["id"] == "traceable_uptake_or_correction" and points == 5 else range(2)
                rating.update(points=points, reason="Authored transcript calibration check.",
                              spans=[{"turn": i, "quote": calls[i]["text"]} for i in indices],
                              source=[{"block": cited_block["id"], "quote": cited_block["text"]}])
        process_marks[packet["id"]] = marks
    process_check = calibrate.score(process_marks, "process")
    assert process_check["correct_labels"] == process_check["target_labels"] == 8
    contrast_scores = action_contrasts.build()["checks"]
    assert contrast_scores["single_choice_and_exact_set"] == {
        "full": (22, 22), "minimum": (21, 20), "sum": (21, 20), "first feasible": (10, 8)}
    answers = [{"id": row["id"], "choice": row["correct"][0], "choices": row["correct"]}
               for row in action_contrasts.build()["key"]]
    assert action_contrasts.score(answers)["total"] == {"n": 22, "selected_correct": 22, "set_correct": 22}
    reject(lambda: action_contrasts.score([*answers[:-1], answers[0]]))
    visibility = information.audit()
    assert all(row["oracle_accuracy_by_visibility"] == {"00": .5, "01": 1., "10": .5, "11": 1.}
               for row in visibility.values())
    replay = replay_syria()
    assert replay == e.read(e.HERE / "replay.json")
    assert replay["arms"]["solo"]["v1_0_released"] == 56
    assert all(r["v1_1_released"] == 0 for r in replay["arms"].values())
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
    bad_point = process["ratings"][0]
    bad_point.update(points=2, source=retained["source"], spans=[{"turn": 2, "quote": "Peru called for Council unity"}])
    reject(lambda: e.process_score(case, calls, process))
    bad_point.update(points=0, source=[], spans=[])
    retained["spans"].append({"turn": 2, "quote": "Peru called for Council unity"})
    assert e.process_score(case, calls, process)["process_30"]["interactions"] == 5

    ideas = process["ideas"]
    ideas.append({"id": "cooperation", "description": "Serbia states its commitment to cooperation",
                  "support": "supported",
                  "source": [{"block": "srb-cooperation", "quote": "meeting its cooperation obligations"}],
                  "mentions": [{"turn": 1, "quote": "meeting its cooperation obligations"},
                               {"turn": 2, "quote": "met its cooperation obligations"}]})
    scored_ideas = e.process_score(case, calls, process)
    assert scored_ideas["distinct_supported_ideas_by_speaker"] == {
        calls[0]["speaker"]: 0, calls[1]["speaker"]: 1,
    }
    assert scored_ideas["supported_note_ideas_retained"] == 1

    _, capped = sample(case, "peer", 0, FULL)
    capped[-1]["termination"] = "cap"
    marked, _ = verdicts(case, capped, full=True)
    assert e.final_score(case, capped, marked)["released_70"] == 0
    return {"cases": len(cases), "families": 5, "scored_software_fixtures": output["scored"],
            "workshop_decision_keys": 4, "fabricated_citation_rejections": failures,
            "negative_gates": ["missing paired run", "call hash from wrong condition",
                               "unresolved decision", "duplicate decision line", "uncited final uptake", "final-only process credit", "truncated final",
                               "incomplete independent reading"],
            "review_round_trip": agreement["counts"],
            "final_judge_anchors": len(calibrate.anchors()),
            "process_judge_anchors": len(process_anchors),
            "process_anchor_label_software_checks": process_check["correct_labels"],
            "action_contrasts": contrast_scores,
            "workshop_visibility": visibility,
            "archived_syria_finals_replayed": sum(r["rows"] for r in replay["arms"].values()),
            "adapter_round_trip": check_adapter()}


if __name__ == "__main__":
    if sys.argv[1:] == ["--adapter"]:
        adapter()
    else:
        e.emit(run())
