"""Test previously frozen MARL routes on the first-pass Haiti field records."""
from collections import defaultdict
import json
import sys
from unittest.mock import patch

import results

HERE = results.HERE
sys.path.insert(0, str(HERE.parent / "colombia2023"))
import roster_shift as shift
from receipt_outcomes import script
from verified_transfer import align

transfer = shift.transfer
relay = shift.relay


def benefits(target, initial, ids, distribution, records, bank):
    quantities = defaultdict(float)
    for pending, (mass, fees, contacts) in distribution.items():
        held = frozenset(ids[i] for i in target if i not in pending)
        label = ",".join(sorted(held))
        packet = records[label]
        quantities["authored_points"] += mass * bank[held]["record_points"]
        quantities["actual_points"] += mass * packet["points"]
        quantities["released_points"] += mass * packet["points"] * packet["release"]
        quantities["release_probability"] += mass * packet["release"]
        quantities["delivered_criteria_complete"] += mass * packet["all_delivered_criteria"]
        quantities["guard_fail_probability"] += mass * (not packet["semantic_guard_clear"])
        quantities["required_source_completion"] += mass * (not pending)
        quantities["source_cost"] += fees
        quantities["contacts"] += contacts
        quantities["writer_output_tokens"] += mass * packet["output_tokens"]
        quantities["writer_input_tokens"] += mass * packet["input_tokens"]
        quantities["writer_calls"] += mass * packet["calls"]
    assert abs(sum(x[0] for x in distribution.values()) - 1) < 1e-9
    anchor = frozenset({ids[initial]})
    quantities["authored_net_gain"] = quantities["authored_points"] - bank[anchor]["record_points"] - quantities["source_cost"]
    quantities["actual_net_gain"] = quantities["actual_points"] - records[ids[initial]]["points"] - quantities["source_cost"]
    return dict(quantities)


def run(evidence=None):
    if evidence is None:
        evidence = results.load(results.EVIDENCE / "results.json")
    docket = results.load(results.writer.CASE)
    bank = results.verified_bank(docket)
    ids = tuple(docket["sources"])
    pseudo = ({name: None for name in ids},)
    with patch.multiple(transfer, named_sources=lambda: ({"haiti": pseudo}, {}), record_bank=lambda _:bank):
        mapping = align.enrich()["families"]["haiti"]
    alignments = {(r["anchor"], *r["other_cards"]): r for r in mapping["rows"]}
    before = shift.actor_policy()
    saved = results.load(HERE.parent / "colombia2023/specialist-fit-results.json")
    after = {transfer.immutable(row["local_state"]): row["probabilities"] for row in saved["policy"]}
    cases = {}
    for name in ("original", "strong_specialist_B", "mislabelled_specialist_B"):
        rows = []
        strength, desk, mode = shift.CONDITIONS[name]
        for target, anchor in relay.SCENARIOS:
            pending = [i for i in target if i != anchor]
            context = alignments[(ids[anchor], *(ids[i] for i in pending))]
            physical = shift.distribution(pending, strength, desk, mode)
            hint = 1 - desk if mode == "wrong_hint" else desk
            routes = {
                "frozen": shift.remap(before, physical, target, anchor, context, (0, 1)),
                "specialist": shift.remap(after, physical, target, anchor, context, (hint, 1 - hint)),
                "best_fixed": script(target, anchor, ids, bank, physical, False),
                "best_adaptive": script(target, anchor, ids, bank, physical, True),
                "pooled_all_three": {frozenset(): (1., 0., 0.)},
            }
            scores = {n: benefits(target, anchor, ids, route, evidence["field_packets"], bank)
                      for n, route in routes.items()}
            rows.append({"anchor": ids[anchor], "target": [ids[i] for i in target], "scores": scores})
        mean = transfer.mean([r["scores"] for r in rows])
        if name == "original":
            assert abs(mean["frozen"]["authored_net_gain"] - mapping["average"]["aligned_joint"]["net_gain_over_anchor"]) < 1e-9
        cases[name] = {"mean": mean, "rows": rows}
    return {"scope": "Haiti is excluded from the two written-vote policy fits. The four routes share the same "
                     "first-pass generated fields. Scripted controls see the true prior and optimize reply priority. "
                     "Their selection uses the authored reference rather than the generated fields. The pooled writer "
                     "receives all three requested cards immediately with a different information budget.",
            "table_alignment": mapping, "conditions": cases}


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, indent=2))
