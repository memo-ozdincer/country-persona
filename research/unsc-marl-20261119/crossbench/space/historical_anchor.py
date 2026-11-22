"""Validate two authored historical rubric anchors with the shared final scorer."""
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "judge"))
from score import score


def compare():
    packet = json.loads((HERE / "historical-task.json").read_text())
    amendment = "Amendment S/2024/323 failed 7–7–1 for insufficient affirmative votes."
    draft = "Draft S/2024/302 failed 13–1–1 because permanent member Russia voted against."
    narrow = "The Japan–US draft focused on the existing Outer Space Treaty."
    broad = "The Chinese and Russian amendment proposed broader measures and work toward binding multilateral agreements."
    japan = "Japan opposed the amendment and backed the draft, favoring its narrower approach and questioning the proposed treaty's verifiability."
    china = "China backed the amendment and abstained on the draft because it sought broader measures."
    overlap = "Both accepted the draft's underlying treaty focus."
    issues = "They differed over the scope of additional measures and the proposed negotiations."
    later = "The separate S/2024/383 failed on 20 May, 7–7–1, for insufficient affirmative votes."
    clear = "These votes created no new Council authorization."
    invented = "With majority support on the April draft, the Council authorized follow-on negotiations."
    items = (
        (amendment, ("apr-amendment",)), (draft, ("apr-final",)), (narrow, ("apr-final", "japan-reason", "china-reason")),
        (broad, ("apr-amendment", "china-reason")), (japan, ("apr-amendment", "apr-final", "japan-reason")),
        (china, ("apr-amendment", "apr-final", "china-reason")), (overlap, ("japan-reason", "china-reason")),
        (issues, ("japan-reason", "china-reason")), (later, ("may-final",)), (clear, ("apr-final", "apr-amendment", "may-final")),
    )
    evidence = {block["id"]: block["text"] for block in packet["evidence"]}

    def citations(ids):
        return [{"block": key, "quote": evidence[key]} for key in ids]

    examples = []
    for field in (clear, invented):
        wrong = field == invented
        request = {**packet, "id": "anchor-2" if wrong else "anchor-1",
                   "answer": " ".join([*(s for s, _ in items[:-1]), field])}
        units = []
        for item, (sentence, ids) in zip(packet["rubric"], items, strict=True):
            contradiction = wrong and item["id"] == "authority"
            units.append({"id": item["id"], "status": "unmet" if contradiction else "met",
                          "source": citations(ids), "response": field if contradiction else sentence,
                          "reason": "The added authorization contradicts the recorded dispositions."
                          if contradiction else item["rule"]})
        verdict = {"id": request["id"], "units": units,
                   "guard": {"status": "failed" if wrong else "clear",
                             "source": citations(("apr-final",)) if wrong else [],
                             "response": field,
                             "reason": "The failed draft did not authorize negotiations."
                             if wrong else "Each act and attribution stays within the supplied record."}}
        result = score(request, verdict)
        assert result["final"]["lower"] == (63 if wrong else 70)
        assert result["strict"] != wrong
        examples.append({"request": request, "authored_verdict": verdict, "score": result})
    return {"scope": "Assistant-authored anchors, validated by the shared scorer. No model or independent review.", "anchors": examples}


if __name__ == "__main__":
    print(json.dumps(compare(), ensure_ascii=False, indent=2))
