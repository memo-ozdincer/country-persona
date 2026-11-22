"""Audit held certificate losses under one-component swaps."""
import json
from pathlib import Path
from collections import Counter

HERE = Path(__file__).resolve().parent


def read(name):
    return json.loads((HERE / name).read_text())


def run():
    original, direct = read("results.json"), read("credit.json")
    rows = original["held"]
    variants = direct["held_actions"]
    effects = Counter()
    proofs = {arm: Counter() for arm in ("joint", "direct_chair", "direct_reply", "both_direct", "public_planner")}
    for i, row in enumerate(rows):
        name = row["key"] + "/" + str(i % 4)
        earlier = row["arms"]
        a = variants["direct_chair_only"][name]
        b = variants["both_direct"][name]
        assert a["choice"] == b["choice"]
        for key, action in (("joint", earlier["learned_team"]), ("public_planner", earlier["public_value_exact_reply"]),
                            ("direct_chair", a), ("direct_reply", variants["direct_reply_only"][name]), ("both_direct", b)):
            label = action["new_disposition_if_delivered"]
            if label:
                proofs[key]["impasse" if label == "I" else "agreement"] += action["completion_probability"]
        if a["new_disposition_if_delivered"] and not b["new_disposition_if_delivered"]:
            effects["certifying_sends_lost"] += 1
            effects[f'{row["family"]}/certifying_sends_lost'] += 1
        if a["useless"] and not b["useless"]:
            effects["unnecessary_sends_removed"] += 1
        assert not b["new_disposition_if_delivered"] or b["sent"]
    prior = original["summary"]["all"]
    new = direct["systems"]["direct_chair_only"]["all"]["learned_team"]
    return {"unique_held_public_presentations": len({r["key"] for r in rows}),
            "held_rate_presentations": len(rows), "expected_proofs_by_outcome": proofs,
            "sender_swap_effect": effects,
            "direct_chair_same_as_public_value_under_joint_responder": new == prior["public_value_fitted_reply"]}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
