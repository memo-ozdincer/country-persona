"""Generate blinded contrast packets and verify span-grounded score anchors."""

import argparse
from hashlib import sha256
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
RELEASE = HERE.parents[1] / "benchmark-v1.5"
CASE = json.loads((HERE / "case.json").read_text())
BASE = (
    "On 9 December 2022 the Council adopted resolution 2664 by 14 votes to zero, with India abstaining.",
    "The Council kept its asset freezes in place while allowing eligible providers to meet basic human needs and deliver timely humanitarian assistance.",
)
ADOPTED = (
    "At adoption the ISIL and Al-Qaida regime's exemption applied for two years, with the Council intending to decide on an extension.",
    "The Council requested provider due diligence to limit prohibited benefits and gave the 1267 Committee a monitoring role.",
)
INDIA = (
    "India raised diversion risks, sought proactive involvement of the 1267 Monitoring Team and robust reporting, and judged those concerns not fully addressed.",
)
SYNTHESIS = (
    "India's call for stronger oversight therefore remained incompletely addressed in its view, despite the monitoring role the Council assigned to the 1267 Committee.",
    "India saw a gap between the adopted committee monitoring and the proactive expert oversight and robust reporting it had sought.",
)
INTEGRATED = (
    "India raised diversion risks and judged that the adopted committee monitoring did not fully meet its call for a proactive 1267 Monitoring Team and robust reporting."
)
CONTROLS = {
    "collective-attribution": (
        "The Council agreed with India that its own oversight fell short of India's requested safeguards.",
        ("safeguards", "india"),
        "India made this assessment in national capacity. The record supplies no collective endorsement.",
    ),
    "no-monitoring": (
        "India's concern persisted because resolution 2664 assigned no monitoring responsibility.",
        ("safeguards", "india"),
        "The adopted resolution assigned monitoring and India considered its own proposals not fully addressed.",
    ),
    "global-expiry": (
        "All humanitarian exemptions created by the resolution were due to expire after two years.",
        ("safeguards",),
        "The two-year provision applied to the 1267/1989/2253 regime at adoption.",
    ),
    "preapproval": (
        "The Council adopted India's requirement that the Monitoring Team clear every aid transfer in advance.",
        ("safeguards", "india"),
        "Neither source supports prior approval of transfers or attributes such a demand to India.",
    ),
}


def scorer():
    spec = importlib.util.spec_from_file_location("frozen_judge_score", RELEASE / "judge_score.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def samples():
    both = BASE + ADOPTED + INDIA
    yield "literal", both, True, True, False, None, 58
    for i, sentence in enumerate(SYNTHESIS, start=1):
        yield f"synthesis-{i}", both + (sentence,), True, True, True, None, 70
    yield "synthesis-integrated", BASE + ADOPTED + (INTEGRATED,), True, True, True, None, 70
    for name, (sentence, blocks, reason) in CONTROLS.items():
        yield name, both + (sentence,), True, True, False, (sentence, blocks, reason), 0
    for adopted, india, removed in ((False, True, "safeguards"), (True, False, "india")):
        visible = BASE + (ADOPTED if adopted else ()) + (INDIA if india else ())
        yield f"without-{removed}", visible, adopted, india, False, None, 40 if india else 48
        present_relation_source = "india" if india else "safeguards"
        fault = (SYNTHESIS[0], (present_relation_source,),
                 f"The sentence joins adopted monitoring to India's position, but {removed} evidence is absent.")
        yield f"without-{removed}-forced", visible + (SYNTHESIS[0],), adopted, india, False, fault, 0


def records():
    judge = scorer()
    bank = {}
    for name, sentences, adopted, india, synthesis, fault, expected in samples():
        answer = " ".join(sentences)
        visible = {row["id"]: row["text"] for row in CASE["evidence"]
                   if (row["id"] != "safeguards" or adopted) and (row["id"] != "india" or india)}
        packet = {
            "id": sha256(json.dumps([visible, answer], sort_keys=True).encode()).hexdigest()[:20],
            "mode": "FINAL",
            "task": CASE["task"],
            "evidence": [{"id": key, "text": text} for key, text in visible.items()],
            "rubric": CASE["rubric"],
            "answer": answer,
        }

        def cite(keys):
            return [{"block": key, "quote": visible[key]} for key in keys]

        marks = {
            "vote": (BASE[0], ("vote",)),
            "scope": (BASE[1], ("scope",)),
            "term": (ADOPTED[0], ("safeguards",)) if adopted else None,
            "safeguards": (ADOPTED[1], ("safeguards",)) if adopted else None,
            "india": ((INTEGRATED if name == "synthesis-integrated" else INDIA[0]), ("india",))
            if india else None,
            "relation": (sentences[-1], ("safeguards", "india")) if synthesis else None,
        }
        units = [
            {"id": key, "status": "met", "source": cite(mark[1]), "response": mark[0],
             "reason": "The exact candidate span states the rubric requirement and the shown evidence supports it."}
            if mark else
            {"id": key, "status": "unmet", "source": [], "response": "",
             "reason": "The candidate supplies no explicit source-supported statement meeting this requirement."}
            for key, mark in marks.items()
        ]
        guard = ({"status": "failed", "response": fault[0], "source": cite(fault[1]), "reason": fault[2]}
                 if fault else {"status": "clear", "response": "", "source": [],
                                "reason": "Every material claim is supported by the supplied record."})
        verdict = {"id": packet["id"], "units": units, "guard": guard}
        result = judge.score(packet, verdict)
        words = len(answer.split())
        assert words <= CASE["word_cap"]
        released = result["final"]["lower"] if result["guard"] == "clear" else 0
        assert released == expected, (name, released, expected)
        bank[name] = {"packet": judge.request(packet), "verdict": verdict, "raw": result["final"]["lower"],
                      "released": released, "words": words}
    assert len({entry["packet"]["id"] for entry in bank.values()}) == len(bank)
    return bank


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--blind", action="store_true", help="Export blinded judge packets ordered by opaque ID.")
    args = parser.parse_args()
    bank = records()
    result = sorted((entry["packet"] for entry in bank.values()), key=lambda p: p["id"]) if args.blind else bank
    print(json.dumps(result, indent=2, ensure_ascii=False))
