"""Extend source-reviewed base grades with blinded marks on the added sentence."""
from copy import deepcopy
import json
from pathlib import Path

from run_bridge import CASE, HERE, PARENT, READ, frozen, prior

JOINT = "fr-ru-scope"


def run():
    verified = READ(HERE / "verified.json")
    native = READ(PARENT / "scores.json")["scores"]
    oracle = READ(PARENT / "oracle.json")["authored_records"]
    notes = READ(HERE / "annotations.json")
    reused = set(READ(HERE / "plan.json")["reused"])
    known = set()
    blocks = {r["id"]: r["text"] for r in frozen.evidence(CASE)}

    def mark(unit):
        status, quote, ids, reason = unit
        return {"status": status, "response": quote, "reason": reason,
                "source": [{"block": i, "quote": blocks[i]} for i in ids]}

    results, banks, by_packet = {}, {}, {}
    for name, row in verified["records"].items():
        bank, method, tag = name.split("/")
        mask = int(tag.split("-")[-1])
        sid = f"{bank}/{method}/{mask}"
        used = verified["bridges"].get(sid)
        calls = [{}, {}, row]
        packet = frozen.final_packet(CASE, calls)
        primary = "compared" if method == "plain" else "verbatim"
        if bank == "native":
            copied = native[f"{primary}/{tag}"]["marks"]
        else:
            copied = oracle[str(mask)]["marks"]
        verdict = deepcopy(copied)
        verdict["id"] = packet["id"]
        units = {unit["id"]: unit for unit in verdict["units"]}
        if bank == "authored":
            units[JOINT].update(status="unmet", response="", source=[],
                                reason="The authored receipt paragraphs are combined without the oracle comparison.")
        if used and sid not in reused:
            if used["text"]:
                chosen = notes[packet["id"]]
                known.add(packet["id"])
                assert set(chosen) == {"units", "guard"}
                for unit, entry in chosen["units"].items():
                    assert unit in units and entry[1] in used["text"] and entry[1]
                    units[unit].update(mark(entry))
                if chosen["guard"] is not None:
                    assert chosen["guard"][1] in used["text"] and chosen["guard"][1]
                    verdict["guard"] = mark(chosen["guard"])
        assert frozen.judge.request(packet) == verified["blind_packets"][packet["id"]]
        scored = frozen.final_score(CASE, calls, verdict)
        if packet["id"] in by_packet:
            previous = by_packet[packet["id"]]
            assert scored["units"] == previous["units"] and scored["guard"] == previous["guard"]
        by_packet[packet["id"]] = scored
        results[name] = {"packet": packet["id"], "marks": verdict, "score": scored,
                         "bridge_words": len(used["text"].split()) if used else 0}
        banks.setdefault(f"{bank}/{method}", []).append(scored["released_70"])
    assert set(notes) == known
    return {"banks": banks, "scores": results,
            "sha256": {p.name: prior.digest(p) for p in (Path(__file__), HERE / "annotations.json", HERE / "verified.json")}}


if __name__ == "__main__":
    frozen.emit(run())
