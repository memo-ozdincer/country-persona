"""Compare one writer per packet with replay of the unchanged single-source bodies."""
from collections import defaultdict
import json

from verified_bank import ANCHORS, HERE, PARTIES

EVIDENCE = HERE / "receipt-evidence"
OVERLAP = {"ADDITIONAL", "A3", "BRAZIL"}


def compose(packet, single, reference, public):
    rows = [single[source] for source in packet]
    proven = {rule for row in rows for rule in row["evidence_spans"]}
    blocks = [public, *(row["body"] for row in rows)]
    # The additional sentence is the earlier authored, source-verified
    # relation. The two audited roles must appear in the generated text.
    can_compare = OVERLAP <= set(packet) and {"brazil_hope", "a3_condition"} <= proven
    if can_compare:
        blocks.append(reference)
        proven.add("common_ground")
    assembled = "\n\n".join(blocks)
    valid = all(r["releasable"] for r in rows) and len(assembled.split()) <= 185
    return {"record": assembled, "points": 7 * len(proven), "releasable": valid,
            "writer_calls": len(rows), "assembled_authored_comparison": can_compare,
            "tokens": sum(r["writer_output_tokens"] for r in rows)}


def run():
    primary = json.loads((EVIDENCE / "results.json").read_text())
    bank = primary["bank"]
    endpoints = {}
    ref = json.loads(ANCHORS.read_text())["reference"]
    reference = ref[ref.rindex("Both supported"):].strip()
    assert {i.strip() for match in PARTIES.finditer(reference) for i in match.group(1).split(",")} == OVERLAP
    public = next(iter(bank.values()))["record"].split("\n\n", 1)[0]
    for key, row in bank.items():
        packet = key.split(",")
        endpoints[key] = compose(packet, bank, reference, public)
        assert endpoints[key]["points"] <= row["licensed_points"]
    summary = {}
    for situation, schedule in primary["routes"].items():
        routes = {}
        for policy in schedule["mean"]:
            total = defaultdict(float)
            for scenario in schedule["rows"]:
                for receipt, chance in scenario[policy]["packet_probabilities"].items():
                    packet = endpoints[receipt]
                    weight = chance / len(schedule["rows"])
                    total["points"] += weight * packet["points"]
                    total["release_probability"] += weight * packet["releasable"]
                    total["release_points"] += weight * packet["points"] * packet["releasable"]
                    total["writer_calls"] += weight * packet["writer_calls"]
                    total["output_tokens"] += weight * packet["tokens"]
            routes[policy] = dict(total)
        summary[situation] = routes
    return {"scope": "Diagnostic replay of already generated source-local bodies. It may use up to three model calls "
                     "and one source-verified authored comparison. This is separate from the one-call primary comparison.",
            "endpoints": endpoints, "summary": summary}


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, indent=2))
