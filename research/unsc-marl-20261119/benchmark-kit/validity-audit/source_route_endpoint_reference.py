"""Compile an authored, receipt-gated reference for each endpoint packet."""
import json
from statistics import mean

from source_route_endpoint import label, suite, traces
from source_route_release import OVERLAP

PUBLIC = (
    "On 18 November 2024, draft S/2024/826, submitted by Sierra Leone and the United Kingdom, "
    "received 14 votes in favour, one against and no abstentions. Russia cast the sole negative vote and China "
    "voted in favour. The permanent-member negative vote blocked adoption [VOTE].",
    "The draft proposed ending hostilities, protecting civilians and facilitating humanitarian access. "
    "It created no Council mandate [TEXT, VOTE].",
)
SOURCES = {
    "RU-A": "Russia warned of outside interference and opposed external accountability mechanisms [RU-A].",
    "RU-B": "Russia said humanitarian measures needed agreement with Sudan's central authorities [RU-B].",
    "CN-A": "China supported a ceasefire and de-escalation to protect civilians, explaining its affirmative vote. "
            "It said some proposals and concerns remained unaddressed [CN-A].",
    "CN-B": "China called for consultation with Sudan's Government and other relevant parties [CN-B].",
}
NEXT = "Analytical suggestion: distinguish possible amendments from action under existing mandates."


def run():
    records = {}
    for row in suite():
        ids = set(row["evidence_ids"])
        comparison = {"RU-B", "CN-B"} <= ids
        if comparison:
            statements = [OVERLAP, "That overlap coexisted with opposite votes on the draft."]
        else:
            statements = [text for key, text in SOURCES.items() if key in ids]
        paragraphs = [*PUBLIC, *statements, NEXT]
        record = " ".join(paragraphs)
        assert len(record.split()) <= 160
        credits = ["D1", "D2", "A1", "A2", "C2", "S1", "S2"]
        credits.extend(unit for proved, unit in (("RU-A" in ids, "P1"), ("CN-A" in ids, "P2"), (comparison, "C1")) if proved)
        records[row["id"].split("/")[-2]] = {
            "sources": row["evidence_ids"], "record": record, "words": len(record.split()),
            "authored_criterion_coverage": credits, "authored_record_points": len(credits) * 7,
        }
    summary = {}
    for arm, rows in traces().items():
        packets = [records[label(row["evidence"])] for row in rows]
        summary[arm] = {
            "authored_mean_record_points": mean(record["authored_record_points"] for record in packets),
            "unit_counts": {unit: sum(unit in record["authored_criterion_coverage"] for record in packets)
                            for unit in ("P1", "P2", "C1")},
        }
    return {"scope": "Authored and source-gated reference control. Criterion coverage is assigned by construction.",
            "packets": records, "arms": summary}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, ensure_ascii=False))
