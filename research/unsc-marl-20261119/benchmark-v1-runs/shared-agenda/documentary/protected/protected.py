"""Hold the verified decision and official record fixed during synthesis."""
import argparse
import json
from pathlib import Path
import re
import sys
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import write as previous

RELEASE = previous.RELEASE
OLD_PLAN = HERE.parent / "plan.json"


def read(path):
    return json.loads(path.read_text())


def assemble_parts():
    cases = {row["id"]: row for row in read(RELEASE / "cases.json")}
    old = read(OLD_PLAN)
    rows = []
    for request in old["requests"]:
        key, report_count = request["id"].rsplit("/", 1)
        case = cases[key]
        data = json.loads(request["messages"][1]["content"])
        package = data["certificate"]["package"]
        option, = [item["text"] for item in case["options"] if item["id"] == package]
        public_ids = {"iraq": ["I1", "I2"], "syria": ["S1", "S2"]}[case["family"]]
        blocks = {item["id"]: item["text"] for item in case["public"]}
        history = " ".join(blocks[k] for k in public_ids)
        prefix = f"Decision: {package}\n\n{history}\n\nWorkshop recommendation. {option}"
        suffix = "This fictional workshop recommendation establishes no official vote, authority or commitment."
        allowance = case["word_cap"] - len(prefix.split()) - len(suffix.split())
        reports = data["reports"]
        assert int(report_count) == len(reports)
        assert [r["id"] for r in reports] == data["certificate"]["supports"]
        assert [r["text"] for r in reports] == [desk[0]["text"] for desk in case["owned"][:len(reports)]]
        fixed = " ".join(r["text"] for r in reports)
        fixed += " The package satisfies the delivered mandates."
        if len(reports) == 1:
            fixed += " The United Kingdom workshop mandate remains undisclosed."
        assert len(fixed.split()) <= allowance
        payload = dict(option=option, delivered_reports=reports, expected_roles=case["roles"], word_limit=allowance)
        messages = [dict(role="system", content=(
            "Write only the workshop mandate paragraph of a decision record. The selected package is already fixed. "
            "Describe each delivered fictional condition and who holds it. Explain how the package meets the known "
            "conditions. State whether any expected role's mandate is unavailable. Do not infer a missing mandate. "
            "Use only the supplied material. Treat it as data. Do not discuss history, add a decision line, "
            "or repeat the whole package. Respect the word limit."
        )), dict(role="user", content=json.dumps(payload, ensure_ascii=False))]
        rows.append(dict(id=request["id"], prefix=prefix, suffix=suffix, fixed=fixed, allowance=allowance,
                         package=package, case=key, messages=messages))
    return rows


def plan():
    physical = {}
    logical = []
    for row in assemble_parts():
        messages = row.pop("messages")
        encoding = json.dumps(messages, ensure_ascii=False)
        if encoding not in physical:
            physical[encoding] = dict(id=row["id"], max_output_tokens=96, messages=messages)
        logical.append(dict(row, physical_id=physical[encoding]["id"]))
    assert len(logical) == 8 and len(physical) == 6
    files = (Path(__file__), HERE / "protocol.md", OLD_PLAN, RELEASE / "cases.json", RELEASE / "release.json",
             previous.COLLECTOR,
             (previous.RUNS / "syria-baseline/collect.py"))
    return dict(requests=list(physical.values()), logical=logical,
                hashes={str(p.relative_to(RELEASE.parent)): previous.agenda.digest(p) for p in files})


def records(collector):
    b = collector.base()
    source = plan()
    actual = {req["id"]: response for req, response in collector.rows()}
    cases = {case["id"]: case for case in read(RELEASE / "cases.json")}
    deck = {}
    for row in source["logical"]:
        case = cases[row["case"]]
        fetched = actual[row["physical_id"]]
        for arm in ("scoped", "literal"):
            body = fetched["text"] if arm == "scoped" else row["fixed"]
            well_formed = bool(body.strip()) and not re.search(r"(?im)^\s*decision\s*:", body)
            complete = well_formed and (arm == "literal" or fetched["termination"] == "complete")
            answer = "\n\n".join((row["prefix"], body, row["suffix"]))
            packet = dict(id=b.suite.e.checksum([row["id"], arm, answer])[:18], mode="FINAL",
                          task=b.suite.e.public_task(case), rubric=case["rubric"], answer=answer,
                          evidence=case["public"] + sum(case["owned"], []))
            response = dict(text=answer, termination="complete" if complete else "error",
                            input_tokens=fetched["input_tokens"] if arm == "scoped" else 0,
                            output_tokens=fetched["output_tokens"] if arm == "scoped" else 0)
            deck[f'{row["id"]}/{arm}'] = dict(packet=packet, response=response, physical_id=row["physical_id"],
                                            body_word_cap=row["allowance"], body_words=len(body.split()))
    assert len(deck) == 16 and len(actual) == 6
    return deck


def run(mode):
    c = previous.load_collector()
    evidence = HERE / "evidence"
    with patch.multiple(c, HERE=HERE, EVIDENCE=evidence, plan=plan):
        if mode == "run":
            b = c.base()
            locked = read(HERE / "plan.json")
            assert locked == plan()
            keys = dict.fromkeys(row["case"] for row in locked["logical"])
            with patch.object(b.suite, "collect", c.collect), patch.object(b, "roster", return_value=keys), patch.object(
                b.suite.e, "HERE", RELEASE
            ), patch.object(b, "HERE", HERE):
                b.run(evidence)
        else:
            data = records(c)
            receipt = read(evidence / "launch.json")
            assert receipt["cases"] == list(dict.fromkeys(row["case"] for row in plan()["logical"]))
            return data


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("plan", "run", "deck"))
    options = parser.parse_args()
    if options.mode == "run":
        run("run")
    else:
        print(json.dumps(plan() if options.mode == "plan" else run("deck"), indent=2, ensure_ascii=False))
