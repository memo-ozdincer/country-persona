"""Create paired authored records and verify benchmark scoring."""
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "judge"))
from score import score

RESPONSE = (
    "On 30 August 2023 the Council voted on two separate drafts. "
    "S/2023/638 failed 13–1–1 because Russia, a permanent member, voted against. "
    "S/2023/639 failed 1–1–13 for insufficient affirmative votes. "
    "France and the UAE sought to renew sanctions and continue the Panel of Experts. "
    "France supported that draft to sustain the peace agreement through the drawdown and abstained on Russia's alternative. "
    "Russia opposed the first draft, supported its own and said the earlier approach had missed Mali's concerns. "
    "The Russian draft proposed a final extension and immediate dissolution of the Panel. "
    "Both texts would have extended sanctions temporarily, with disagreement over the Panel and whether renewal would be final. "
)
CLEAR = "Neither draft was adopted or authorized new measures."
FABRICATED = "Neither draft was adopted, but the recorded majority on S/2023/638 itself authorized an extension of sanctions."
ANCHORS = (
    ("S/2023/638 failed 13–1–1 because Russia, a permanent member, voted against.", ("status-638",)),
    ("S/2023/639 failed 1–1–13 for insufficient affirmative votes.", ("status-639",)),
    ("France and the UAE sought to renew sanctions and continue the Panel of Experts.", ("status-638",)),
    ("The Russian draft proposed a final extension and immediate dissolution of the Panel.", ("status-639",)),
    ("France supported that draft to sustain the peace agreement through the drawdown and abstained on Russia's alternative.",
     ("status-638", "status-639", "french-uae")),
    ("Russia opposed the first draft, supported its own and said the earlier approach had missed Mali's concerns.",
     ("status-638", "status-639", "russia")),
    ("Both texts would have extended sanctions temporarily", ("status-638", "status-639")),
    ("with disagreement over the Panel and whether renewal would be final", ("status-638", "status-639")),
    ("the Council voted on two separate drafts", ("status-638", "status-639")),
    (CLEAR, ("status-638", "status-639")),
)


def build():
    packet = json.loads((HERE / "historical-task.json").read_text())
    blocks = {x["id"]: x["text"] for x in packet["evidence"]}
    result = []
    for index, end in enumerate((CLEAR, FABRICATED)):
        bad = index == 1
        request = {**packet, "answer": RESPONSE + end, "id": f"mali-anchor-{index+1}"}
        units = []
        for rubric, (phrase, ids) in zip(packet["rubric"], ANCHORS, strict=True):
            fails = bad and rubric["id"] == "authority"
            units.append({"id": rubric["id"], "status": "unmet" if fails else "met",
                          "response": end if fails else phrase,
                          "source": [{"block": i, "quote": blocks[i]} for i in ids],
                          "reason": "The final sentence attributes an authorization to the failed vote." if fails else rubric["rule"]})
        verdict = {"id": request["id"], "units": units,
                   "guard": {"status": "failed" if bad else "clear", "response": end,
                             "source": [{"block": "status-638", "quote": blocks["status-638"]}] if bad else [],
                             "reason": "The chair reports failure despite the numerical majority." if bad else "The two dispositions remain distinct."}}
        rating = score(request, verdict)
        assert rating["final"]["lower"] == (63 if bad else 70)
        assert rating["strict"] == (not bad)
        result.append({"request": request, "authored_verdict": verdict, "scores": rating})
    return {"scope": "Assistant-authored contrast and shared scorer validation. No model or independent judging.", "anchors": result}


if __name__ == "__main__":
    print(json.dumps(build(), ensure_ascii=False, indent=2))
