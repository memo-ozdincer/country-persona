"""Replay a reviewed, owner-bound composer on the same eight note pairs."""
from collections import defaultdict
import json
from pathlib import Path

import chair_scope as study
from score_scope import ACTIONS, effects

HERE, CASE, e = study.HERE, study.CASE, study.e
PUBLIC = (
    "The Council adopted Japanese–US draft S/2024/500 as resolution 2739 (2024), 12–0–3. "
    "Algeria, China and Russia abstained. It extended the Secretary-General’s reporting request "
    "under paragraph 10 of resolution 2722 (2024) through 15 January 2025, without granting "
    "new authority for military action."
)
# Each allowed fragment is an exact extraction with a reviewed source witness.
# The units tuple lists only additional full-credit criteria established by that fragment.
RECEIPTS = (
    (0, "sponsors", "US/Japan sought accurate data.", ()),
    (0, "sponsors", "The US and Japan supported draft S/2024/500 to extend reporting until 15 Jan 2025 and demand Houthi cessation, citing threats to commerce.", ()),
    (0, "sponsors", "Japan and the United States supported the extension so the Council would have accurate and timely information on the attacks for future deliberations.",
     ("sponsor-reason",)),
    (1, "algeria", "Algeria abstained, citing concerns over implementation of resolution 2722 and misuse of self-defence.", ()),
    (1, "algeria", "Algeria abstained, citing unresolved implementation of Res. 2722 and misuse of self-defence.", ()),
    (1, "algeria", "Algeria valued monthly reporting on attacks on merchant and commercial vessels to keep the Council informed. "
     "It abstained over implementation of resolution 2722 and alleged misuse or misinterpretation of self-defence through attacks on sovereign territory.",
     ("algeria-reason",)),
)
CORE = {
    "disposition": ("vote", "adopted Japanese–US draft S/2024/500 as resolution 2739 (2024), 12–0–3. Algeria, China and Russia abstained."),
    "draft-and-sponsors": ("vote", "Japanese–US draft S/2024/500"),
    "operative-report": ("action", "extended the Secretary-General’s reporting request under paragraph 10 of resolution 2722 (2024) through 15 January 2025"),
    "authority": ("action", "without granting new authority for military action"),
}


def deliver(note):
    eligible = [(block, passage, units) for role, block, passage, units in RECEIPTS
                if note["speaker"] == CASE["roles"][role] and passage in note["text"]]
    assert len(eligible) <= 1
    return eligible


def bind(notes):
    fragments = [receipt for note in notes for receipt in deliver(note)]
    assert len({block for block, _, _ in fragments}) == len(fragments)
    return fragments


def score(notes):
    pieces = bind(notes)
    verified = CORE | {unit: (block, phrase) for block, phrase, units in pieces for unit in units}
    text = "\n\n".join([PUBLIC, *(phrase for _, phrase, _ in pieces)])
    result = {"text": text, "termination": "complete"}
    calls = [{}, {}, result]
    packet = e.final_packet(CASE, calls)
    blocks = e.judge.by_id(packet["evidence"])
    verdict = {"id": packet["id"], "units": [], "guard": {
        "status": "clear", "source": [], "response": "",
        "reason": "The public disposition and all admitted role-local excerpts are supported by the case evidence."}}
    for rubric in CASE["rubric"]:
        key = rubric["id"]
        if key in verified:
            block, quote = verified[key]
            sources = [{"block": block, "quote": blocks[block]["text"]}]
            status, reason = "met", rubric["rule"]
        else:
            sources, quote = [], ""
            status, reason = "unmet", "The admitted excerpts omit part or all of this requirement."
        verdict["units"].append({"id": key, "response": quote, "source": sources, "status": status, "reason": reason})
    final = e.final_score(CASE, calls, verdict)
    assert final["release"] and final["released_70"] == final["raw_70"][0]
    return {"record": text, "score": final, "verdict": verdict,
            "admitted": [{"block": block, "excerpt": phrase} for block, phrase, _ in pieces]}


def run():
    rows, by_order = {}, defaultdict(dict)
    for key, request in study.cases():
        notes = json.loads(request["messages"][1]["content"])["notes"]
        result = rows[key] = score(notes)
        order, action = key.split("/")
        by_order[order][action] = result["score"]["released_70"]
        assert bind([dict(note, speaker=CASE["roles"][1 - CASE["roles"].index(note["speaker"])])
                     for note in notes]) == []
        for note in notes:
            assert not deliver({**note, "text": "No scoped statement available."})
    assert all(tuple(actions) == ACTIONS for actions in by_order.values())
    filenames = (Path(__file__), HERE / "plan.json", HERE.parent / "verified.json")
    return {"scope": "reviewed source-bound comparator and authored public block",
            "outcomes": rows, "released_effects": {order: effects(matrix) for order, matrix in by_order.items()},
            "sources_sha256": {str(path.relative_to(HERE.parent)): study.pin(path) for path in filenames}}


if __name__ == "__main__":
    e.emit(run())
