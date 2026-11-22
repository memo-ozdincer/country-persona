"""Apply the frozen quote contract to saved prospective records."""
import argparse
import json
from pathlib import Path

from live_tolerance import CASE, HERE, READ, frozen, prior


def packets():
    native = READ(HERE / "verified.json")
    return native["blind_packets"]


def score():
    native = READ(HERE / "verified.json")
    annotations = READ(HERE / "annotations.json")
    blocks = frozen.judge.by_id(frozen.evidence(CASE))
    assert set(annotations) == set(native["blind_packets"])
    result = {}
    for arm, record in native["records"].items():
        if arm.startswith("note/"):
            continue
        calls = [{}, {}, record]
        packet = frozen.final_packet(CASE, calls)
        assert frozen.judge.request(packet) == native["blind_packets"][packet["id"]]
        marks = annotations[packet["id"]]
        units = []
        for criterion in CASE["rubric"]:
            unit = criterion["id"]
            status, claim, sources, reason = marks["criteria"][unit]
            units.append({"id": unit, "status": status, "response": claim,
                          "source": [{"block": b, "quote": blocks[b]["text"]} for b in sources],
                          "reason": reason})
        status, claim, sources, reason = marks["guard"]
        verdict = {"id": packet["id"], "units": units,
                   "guard": {"status": status, "response": claim, "reason": reason,
                             "source": [{"block": b, "quote": blocks[b]["text"]} for b in sources]}}
        score = frozen.final_score(CASE, calls, verdict)
        visible = {r["id"] for r in CASE["public"]}
        if arm.startswith("mask-"):
            mask = int(arm.split("-")[-1])
            visible.update(r["id"] for i, own in enumerate(CASE["owned"]) if mask & (1 << i) for r in own)
        else:
            visible.update(blocks)
        unsupported_visibility = sorted({citation["block"] for row in units if row["status"] == "met"
                                        for citation in row["source"] if citation["block"] not in visible})
        result[arm] = {"packet": packet["id"], "score": score, "marks": verdict,
                       "met_source_ids_outside_receipt": unsupported_visibility}
    return {"scores": result, "score_bank": [result[f"mask-{i}"]["score"]["released_70"] for i in range(8)],
            "sha256": {p.name: prior.digest(p) for p in
                       (Path(__file__), HERE / "verified.json", HERE / "annotations.json", HERE / "docket.json")}}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("packets", "score"))
    print(json.dumps({"packets": packets, "score": score}[parser.parse_args().mode](), ensure_ascii=False, indent=2))
