"""Render source-gated reference records for the Venezuela evidence routes."""
import json
from itertools import product
from pathlib import Path

from duplicate_card_routes import CASE

FIT = Path(__file__).resolve().parent.parent / "evidence/duplicate-card-routes/fit.json"
CARD_IDS = (None, "CHAIR", "INDONESIA")
HEAD = (
    "On 28 February 2019, the U.S. draft S/2019/186 failed 9–3–3 due to permanent-member vetoes by China and Russia [US-VOTE]. "
    "The Russian draft S/2019/190 failed 4–7–4 for lack of affirmative votes [RU-VOTE]. "
    "The U.S. draft proposed a peaceful electoral process with international observation. "
    "The Russian draft supported inclusive dialogue, including the Montevideo Mechanism [US-TEXT, RU-TEXT]. "
    "Both addressed humanitarian assistance. The U.S. text proposed unhindered access. The Russian text called for government leadership and consent [US-TEXT, RU-TEXT]."
)
TAIL = "Neither draft created Council authority. Analytical suggestion: compare the proposals for areas that could be discussed separately."
BODY = {
    "CHAIR": "Ndong Mba announced both votes as Council President. Equatorial Guinea abstained on the U.S. text and backed the Russian text [CHAIR].",
    "INDONESIA": "Indonesia abstained on both and urged inclusive dialogue and acceptance of the Secretary-General’s good offices [INDONESIA].",
}


def packets():
    case = json.loads(CASE.read_text())
    for received in ((), ("CHAIR",), ("INDONESIA",), ("CHAIR", "INDONESIA")):
        yield received, {**case["public"], **{card: case["cards"][card]["text"] for card in received}}


def run():
    case = json.loads(CASE.read_text())
    distribution = json.loads(FIT.read_text())
    measures = {}
    records = []
    for received, packet in packets():
        record = " ".join([HEAD, *(BODY[card] for card in received), TAIL])
        units = [key for key in case["criteria"] if key not in ("P1", "P2")]
        units.extend(case["cards"][card]["criterion"] for card in received)
        assert len(record.split()) <= 160 and len(units) == 8 + len(received)
        records.append({"received": list(received), "sources": list(packet),
                        "reference": record, "words": len(record.split()),
                        "criteria_by_construction": units, "points": 7 * len(units)})
    for prior, arms in distribution["arms"].items():
        summary = {}
        for arm, results in arms.items():
            counts = {card: 0.0 for card in BODY}
            both = 0.0
            for row in results["worlds"]:
                ids = {CARD_IDS[action] for action in row["actions"]} - {None}
                for card in ids:
                    counts[card] += row["probability"]
                if len(ids) == 2:
                    both += row["probability"]
            expected = 56 + 7 * sum(counts.values())
            assert abs(expected - results["authored_reference_points"]) < 1e-9
            summary[arm] = {"reference_points": expected, "claim_supply_probability": counts,
                            "both_card_probability": both, "net": results["net"]}
        measures[prior] = summary
    # Carry all possible views, including an empty receipt.
    assert len(records) == len(list(product((0, 1), repeat=2)))
    return {"scope": "Authored exact-source references. Criteria are assigned by construction, without independent reviewing.",
            "records": records, "measures": measures}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, ensure_ascii=False))
