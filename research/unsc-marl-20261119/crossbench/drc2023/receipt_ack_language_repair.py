"""Isolate which receipt-reading errors erase the learned handoff advantage."""
import json

import receipt_ack_language as study

EVIDENCE = study.HERE / "receipt-ack-language-evidence/results.json"
FIELDS = study.FIELDS


def run():
    scored = study.load(EVIDENCE)
    actions = {tuple(row["condition"]): row["choices"] for row in scored["actions"]}
    decoder = {tuple(row["condition"]): row["choices"] for row in scored["decode"]}
    changes = {"measured": (), "report_only": (FIELDS.index("REPORT"),),
               "non_targets": (FIELDS.index("TERM"), FIELDS.index("CONSULT")), "all": range(len(FIELDS))}
    results = {}
    for name, slots in changes.items():
        altered = decoder | {("received", index): [index] * 2 for index in slots}
        replay = study.replay(actions, altered, False)
        results[name] = {context: row["decoded_learned"] for context, row in replay.items()}
        if name == "measured":
            assert replay == scored["replay"]["ordinary"]
        if name == "all":
            assert all(row["decoded_learned"] == row["host_typed_learned"] for row in replay.values())
    return {"scope": "Counterfactual repairs in deterministic replay. No repaired decoder or additional model call.",
            "source_sha256": study.sha256(EVIDENCE.read_bytes()).hexdigest(), "results": results}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
