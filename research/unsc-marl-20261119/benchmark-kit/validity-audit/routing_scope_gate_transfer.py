"""Test a two-check release gate on new climate paraphrases and UNIFIL scope controls."""
import argparse
import json
from pathlib import Path
from unittest.mock import patch

import routing_climate_gate_replay as replay
import routing_climate_scope_gate as climate

affirmative, read, digest, runner = climate.affirmative, climate.read, climate.digest, climate.runner
BASE = climate.MAIN.parent / "climate2021-scope-gate"
UNIFIL = affirmative.UNIFIL
SCOPE_SYSTEM = (
    "Read only the candidate. Report what extent it ascribes to Brazil's assessment. "
    "Addressing some concerns, without claiming that none remained, is different from addressing all concerns. "
    "Decide what the candidate asserts about the concerns. Output YES or NO."
)
SCOPE_QUESTIONS = (
    "Does the candidate attribute a claim that every Lebanese concern was addressed to Brazil?",
    "Does the candidate say that in Brazil's view the text left no Lebanese concern unaddressed?",
)


def panel():
    sources = {row["id"]: row["text"] for row in climate.transfer.task()["optional_sources"]}
    sahel = sources["india-explanation"] + " " + sources["russia-explanation"]
    unifil_source = next(row["text"] for row in read(UNIFIL)["evidence"] if row["id"] == "brazil")
    return [
        ("sahel", "included-risk", "The regional security draft for the Sahel considered climate change as one factor in a wider set of risks.", sahel, True),
        ("sahel", "territorial-boundary", "India's preferred alternative was a security draft confined geographically to the Sahel.", sahel, True),
        ("sahel", "direct-contrast", "The proposed alternative limited its geographic focus to the Sahel while addressing several security pressures, including climate.", sahel, True),
        ("sahel", "nonweather-excluded", "The proposal focused on the Sahel and put security pressures unrelated to the weather outside its remit.", sahel, False),
        ("sahel", "sole-policy-topic", "India supported a Sahel-specific draft whose sole policy topic was climate-induced insecurity.", sahel, False),
        ("sahel", "no-other-issues", "The Sahel alternative addressed climate pressures to the exclusion of other security concerns.", sahel, False),
        ("unifil", "part-of", "Brazil said the draft addressed a portion of Lebanon's concerns.", unifil_source, True),
        ("unifil", "at-least-some", "Brazil thought the French text addressed at least some concerns raised by Lebanon.", unifil_source, True),
        ("unifil", "some-with-support", "Brazil supported UNIFIL continuing its work and said the text addressed some Lebanese concerns.", unifil_source, True),
        ("unifil", "none-outstanding", "Brazil believed the text left no Lebanese concern outstanding.", unifil_source, False),
        ("unifil", "whole-list", "Brazil said the compromise took care of the whole list of Lebanon's concerns.", unifil_source, False),
        ("unifil", "all-with-support", "Brazil supported UNIFIL continuing its work and said the text addressed all Lebanese concerns.", unifil_source, False),
    ]


def requests():
    for docket, name, claim, evidence, _ in panel():
        for i, question in enumerate(affirmative.QUESTIONS):
            yield affirmative.make_request(f"{docket}/{name}/support-{i}", claim, evidence, question)
        system, questions = ((climate.EXTRACTION_SYSTEM, climate.EXTRACTION_QUESTIONS) if docket == "sahel"
                             else (SCOPE_SYSTEM, SCOPE_QUESTIONS))
        for i, question in enumerate(questions):
            body = {"candidate_sentence": claim, "question": question}
            yield {"id": f"{docket}/{name}/restriction-{i}", "cap": 4, "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": json.dumps(body, ensure_ascii=False)},
            ]}


def locks():
    return {**climate.locks(), "transfer_script": digest(Path(__file__)), "unifil_source": digest(UNIFIL),
            "calibration": digest(BASE / "scores.json")}


def episode(generate):
    plans = list(requests())
    outcomes = {}
    for start in range(0, len(plans), 12):
        outcomes.update(generate(plans[start:start + 12]))
    return [{"family": "transferred-scope-gate", "final": outcomes}]


def admissions(support, restriction):
    return {"support_only": support == [True, True], "restriction_only": restriction == [False, False],
            "both": support == [True, True] and restriction == [False, False]}


def score(directory):
    assert read(directory / "launch.json")["sha256"] == locks()
    trace, finals = directory / "transcript.jsonl", directory / "final-records.json"
    done = read(directory / "complete.json")
    assert digest(trace) == done["transcript_sha256"] and digest(finals) == done["final_records_sha256"]
    rows = list(map(json.loads, trace.read_text().splitlines()))
    assert len(rows) == done["records"]
    for row, plan in zip(rows, requests(), strict=True):
        assert all(row[k] == value for k, value in plan.items())
    raw = {row["id"]: row["output"] for row in rows}
    assert read(finals)["transferred-scope-gate"] == raw
    records = []
    for docket, name, claim, _, allowed in panel():
        answers = {mode: [raw[f"{docket}/{name}/{mode}-{i}"] for i in range(2)]
                   for mode in ("support", "restriction")}
        yes = {mode: [affirmative.factored.normalized(a, 0) for a in values] for mode, values in answers.items()}
        records.append({"docket": docket, "control": name, "claim": claim, "correct_to_release": allowed,
                        "judgments": answers, "release": admissions(**yes)})
    summary = {}
    for docket in ("sahel", "unifil"):
        cases = [r for r in records if r["docket"] == docket]
        summary[docket] = {
            mode: {"clear_controls_released": sum(r["correct_to_release"] and r["release"][mode] for r in cases),
                   "unsupported_controls_released": sum(not r["correct_to_release"] and r["release"][mode] for r in cases)}
            for mode in cases[0]["release"]
        }

    # Replicate the established attribution replay under the frozen two-check rule.
    calibrated = read(BASE / "scores.json")
    labels = {r["key"]: {**r, "model_blocks_by_method": {
        "both": not all(r["model_blocks_by_method"][mode] is False for mode in ("support", "restriction"))
    }} for r in calibrated["items"]}
    old = replay.transfer.captured(replay.MAIN, replay.PLAN)
    marks = read(replay.MAIN / "annotations.json")
    _, decisions = replay.apply_gate(old, marks, labels, "both")
    return {
        "scope": "Fix the combined rule after the first panel, then evaluate new authored sentences with the same "
                 "climate questions and an adapted extent extractor for Brazil's UNIFIL explanation. Controls are "
                 "not independent historical families. The earlier paired route replay remains a development audit.",
        "trace_sha256": digest(trace), "summary": summary, "records": records, "archived_decisions": decisions,
    }


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("mode", choices=("check", "run", "score"))
    cli.add_argument("directory", type=Path, nargs="?")
    args = cli.parse_args()
    if args.mode == "run":
        with patch.object(runner, "episode", episode), patch.object(runner, "locks", locks):
            runner.run(Path(read(climate.MODEL)["model"]), args.directory)
    elif args.mode == "score":
        print(json.dumps(score(args.directory), indent=2, ensure_ascii=False))
    else:
        plans = list(requests())
        assert len(plans) == len({p["id"] for p in plans}) == 48
        print(json.dumps({"cases": len(panel()), "calls": len(plans), "locks": locks()}, indent=2))
