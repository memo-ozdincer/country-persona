"""Run paired native delegation summaries with a verbatim public lead."""
import argparse
from importlib.util import module_from_spec, spec_from_file_location
import json
from pathlib import Path
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
PARENT = HERE.parent
spec = spec_from_file_location("evidence_2553_writer_anchor", PARENT / "writer.py")
baseline = module_from_spec(spec)
spec.loader.exec_module(baseline)

SYSTEM = (
    "Write the delegation-comments section of a neutral record. Use only the supplied "
    "delegation notes. In at most 75 words, report each speaker's position and qualifications. "
    "When two delivered notes address the same specific issue, state their overlap or "
    "distinction precisely and preserve both speakers' own reasons. Attribute every claim "
    "to the speaker who made it. End after the delegation comments."
)


def plan():
    template = baseline.locked()
    public = baseline.CASE["public"]
    lead = " ".join(row["text"] for row in public)
    for row in template["requests"].values():
        request = row["request"]
        notes = json.loads(request["messages"][1]["content"])["delivered"]
        assert len(notes) >= 1
        request["messages"] = [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": json.dumps({"delivered_notes": notes}, ensure_ascii=False)},
        ]
    template["public_lead"] = lead
    template["pins"].update({str(p.relative_to(baseline.RUNS.parent)): baseline.pin(p)
                             for p in (Path(__file__), HERE / "protocol.md", PARENT / "plan.json",
                                       PARENT / "authority-clarification/scores.json")})
    return template


def locked():
    result = plan()
    assert result == baseline.test.READ(HERE / "plan.json")
    return result


def act(mode):
    command = locked()
    with patch.object(baseline, "HERE", HERE), patch.object(baseline, "OUT", HERE / "evidence"), patch.object(
            baseline, "locked", return_value=command):
        if mode == "run":
            baseline.run()
            return
        verified = baseline.verify()
    composed = {}
    for key, row in verified["packets"].items():
        draft = row["reply"]
        composed[key] = {**row, "reply": draft | {
            "text": command["public_lead"] + "\n\n" + draft["text"],
            "termination": draft["termination"] if 0 < len(draft["text"].split()) <= 75 else "error",
        }}
    print(json.dumps({"packets": composed, "native_sections": verified["packets"],
                      "manifest": verified["manifest"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("plan", "run", "verify"))
    mode = parser.parse_args().mode
    if mode == "plan":
        print(json.dumps(plan(), ensure_ascii=False, indent=2))
    else:
        act(mode)
