"""Exercise the judge contract with authored good, bad, and peer-credit anchors."""
from copy import deepcopy
import json
from pathlib import Path
import sys

from score import request, score

HERE = Path(__file__).resolve().parent


def citation(block, quote):
    return [{"block": block, "quote": quote}]


def anchor(id_, source_blocks, keys, answers):
    criteria = [{"id": name, "category": "final", "weight": 14, "rule": rule}
                for name, rule, _, _ in keys]
    task = "Write a retrospective decision record based on the supplied roll call and statements."
    episodes = []
    for suffix, answer, adverse_claim in answers:
        opaque_id = f"{id_}-{suffix}"
        packet = {"id": opaque_id, "mode": "FINAL", "task": task, "evidence": source_blocks,
                  "rubric": criteria, "answer": answer}
        grades = []
        for name, rule, block, (source, correct, incorrect) in keys:
            text = incorrect if adverse_claim else correct
            grades.append({"id": name, "status": "met" if not adverse_claim or text == correct else "unmet",
                           "source": citation(block, source), "response": text,
                           "reason": rule if not adverse_claim or text == correct else "The answer fails this requirement."})
        if adverse_claim:
            claim, source_id, exact_source = adverse_claim
            guard = {"status": "failed", "source": citation(source_id, exact_source),
                     "response": claim, "reason": "Material public-record attribution contradicted by supplied evidence."}
        else:
            guard = {"status": "clear", "source": [], "response": "",
                     "reason": "Statements and recommendations remain within the supplied scope."}
        verdict = {"id": opaque_id, "units": grades, "guard": guard}
        episodes.append({"request": request(packet), "authored_verdict": verdict, "score": score(packet, verdict)})
    return episodes


def build():
    benchmark = json.loads((HERE / "benchmark-development.json").read_text())
    assert [row["draft"] for row in benchmark["rows"]] == ["S/2022/925", "S/2023/970"]
    primary = [row["primary_vote_record"] for row in benchmark["rows"]]
    sanction_blocks = [
        {"id": "roll", "url": primary[0], "text": "S/2022/925 was adopted 14–0–1. Brazil voted yes. India abstained."},
        {"id": "india", "url": "https://docs.un.org/en/S/PV.9214", "text": "India sought proactive monitoring by the 1267 Monitoring Team and robust reporting. It said the adopted text did not fully address these requests."},
        {"id": "authority", "url": primary[0], "text": "A possible future implementation review is distinct from this adoption and establishes no future endorsement."},
    ]
    sanctions = anchor("T17", sanction_blocks, [
        ("disposition", "Report adoption and exact tally.", "roll", ("was adopted 14–0–1", "Adopted 14–0–1.", "Adopted 14–0–1.")),
        ("del_vote", "Identify Brazil's yes vote and India's abstention.", "roll", ("Brazil voted yes. India abstained.", "Brazil voted yes and India abstained.", "India endorsed it alongside Brazil.")),
        ("safeguard", "Identify India's Monitoring Team and reporting request.", "india", ("proactive monitoring by the 1267 Monitoring Team and robust reporting", "India sought proactive 1267 Monitoring Team oversight and robust reporting", "")),
        ("unresolved", "State the monitoring and reporting requests were not fully addressed.", "india", ("did not fully address these requests", "those requests were not fully addressed", "the text met India's requests")),
        ("authority", "Bound claims to recorded acts or explicitly labeled future proposals.", "authority", ("establishes no future endorsement", "A future review could revisit those provisions; no future endorsement is established.", "")),
    ], [
        ("2", "Adopted 14–0–1. Brazil voted yes and India abstained. India sought proactive 1267 Monitoring Team oversight and robust reporting; those requests were not fully addressed. A future review could revisit those provisions; no future endorsement is established.", None),
        ("7", "Adopted 14–0–1. India endorsed it alongside Brazil. The group agreed that the text met India's requests.", ("India endorsed it alongside Brazil.", "roll", "India abstained.")),
    ])

    gaza_blocks = [
        {"id": "roll", "url": primary[1], "text": "The draft received 13 yes, one no and one abstention. The United States voted no and the veto prevented adoption. France and Brazil voted yes. The United Kingdom abstained."},
        {"id": "scope", "url": primary[1], "text": "India was not a Council member at this meeting. The packet does not supply a national statement by India."},
        {"id": "uk", "url": primary[1], "text": "The United Kingdom said it could not vote for a draft that did not condemn the Hamas attacks. The statement does not establish a vote for any future amended draft."},
    ]
    gaza = anchor("K44", gaza_blocks, [
        ("disposition", "Report the 13–1–1 tally and non-adoption.", "roll", ("13 yes, one no and one abstention", "The draft failed despite a 13–1–1 tally.", "")),
        ("veto", "Identify the US veto as the cause of non-adoption.", "roll", ("the veto prevented adoption", "The United States veto blocked it.", "")),
        ("del_vote", "Separate France and Brazil's affirmative votes from the UK's abstention.", "roll", ("France and Brazil voted yes. The United Kingdom abstained.", "France and Brazil voted yes; the United Kingdom abstained.", "France, Brazil and the United Kingdom endorsed the text.")),
        ("membership", "Describe India's absence from the Council rather than recording a vote.", "scope", ("India was not a Council member", "India was not a Council member.", "India abstained.")),
        ("future", "Avoid predicting a newly official vote from the UK's explanation.", "uk", ("does not establish a vote for any future amended draft", "a future vote remains unknown", "the United Kingdom would definitely vote yes")),
    ], [
        ("5", "The draft failed despite a 13–1–1 tally. The United States veto blocked it. France and Brazil voted yes; the United Kingdom abstained. India was not a Council member. The UK cited the absence of a condemnation of the Hamas attacks; a future vote remains unknown.", None),
        ("1", "The draft passed. France, Brazil and the United Kingdom endorsed the text. India abstained. With a condemnation clause, the United Kingdom would definitely vote yes.", ("India abstained.", "scope", "India was not a Council member")),
    ])

    item = {"id": "E3", "peer": "The UK abstained; do not count it as an affirmative vote.",
            "opening": "The UK vote is not stated here.", "solo_revision": "The UK procedure is unclear.",
            "revision": "The UK abstained, so it must be listed separately from the affirmative votes."}
    packet = {"id": "R28", "mode": "MECHANISM", "task": "Trace a specific change to a peer correction.",
              "evidence": gaza_blocks, "opportunities": [item]}
    verdict = {"id": "R28", "opportunities": [{"id": "E3", "status": "used", "peer_specific": True,
               "peer": "The UK abstained", "revision": "The UK abstained, so it must be listed separately",
               "source": citation("roll", "The United Kingdom abstained."),
               "reason": "The peer supplies the specific correction that appears with a reason only in the peer revision."}]}
    assert score(packet, verdict) == {"opportunities": 1, "credited": 1}
    malformed = deepcopy(verdict)
    malformed["opportunities"][0]["source"][0]["quote"] = "India endorsed the text."
    missing_history = deepcopy(packet)
    del missing_history["opportunities"][0]["solo_revision"]
    for given_packet, given_verdict in ((packet, malformed), (missing_history, verdict)):
        try:
            score(given_packet, given_verdict)
        except ValueError:
            pass
        else:
            raise AssertionError("Malformed citation or causal claim accepted")
    assert [v["score"]["strict"] for v in sanctions + gaza] == [True, False, True, False]
    return {
        "scope": "Authored calibration and software validation; no judge endpoint was called.",
        "final_calibration": sanctions + gaza,
        "mechanism_calibration": {"request": request(packet), "authored_verdict": verdict, "score": score(packet, verdict)},
        "negative_checks": ["Invented evidence citation rejected", "Peer-specific credit without matched solo history rejected"],
    }


if __name__ == "__main__":
    with Path(sys.argv[1]).open("x") as output:
        json.dump(build(), output, indent=2, ensure_ascii=False)
        output.write("\n")
