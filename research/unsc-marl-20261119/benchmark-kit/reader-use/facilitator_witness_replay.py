"""Replay the same selectors with and without the new witness reader."""
from collections import defaultdict
from hashlib import sha256
import json

import facilitator_witness as study

HERE = study.HERE
ARTIFACT = HERE / "facilitator-witness-evidence/results.json"
TRANSFER = HERE / "facilitator-policy-transfer-evidence/results.json"


def run(judged=None):
    transfer = study.transfer
    evidence = transfer.protocol.delivery.load(ARTIFACT)
    rows = evidence["full_packet_decisions"]
    initial = transfer.protocol.delivery.load(TRANSFER)
    params = transfer.policy(transfer.FROZEN)
    panel_ids = [(family, number) for family, proposals in transfer.PANELS.items()
                 for number, _ in enumerate(proposals)]
    controls = {}
    for inventory in ("overlap", "split"):
        controls[inventory] = {}
        for name in ("learned", "learned_erased", "greedy"):
            compare = {}
            methods = ("original", "ungated", "witness", "semantic_veto", "perfect")
            for method in methods + tuple(judged or {}):
                value = defaultdict(float)
                for (family, case), panel, prior in zip(panel_ids, rows, initial["panels"], strict=True):
                    assert family == panel["family"] and panel["proposal"] == prior["proposal"]
                    truth = tuple(panel["truth"])
                    local = [evidence["reads"][f"{family}/{case}/{i}"] for i in range(2)]
                    assert tuple(row["expected"] for row in local) == truth
                    alternatives = {
                        "original": tuple(prior["observed_relations"]),
                        "ungated": tuple(row["proposed_label"] or "unknown" for row in local),
                        "witness": tuple(panel["admitted"]),
                        "semantic_veto": tuple(label if label == gold else "unknown"
                                               for label, gold in zip(panel["admitted"], truth, strict=True)),
                        "perfect": truth,
                    }
                    if method in alternatives:
                        observed = alternatives[method]
                    else:
                        observed = tuple(judged[method][f"{family}/{case}/{i}"] for i in range(2))
                    scores, receipts = transfer.base.distribution(name, params, transfer.base.base.roster(inventory), truth, observed)
                    scale = 1 / len(rows)
                    value["cost"] += scores["cost"] * scale
                    for seen, p in receipts.items():
                        gold, claimed = (transfer.base.decision(relations, seen) for relations in (truth, observed))
                        value["true_retain"] += scale * p * (gold == claimed == "retain")
                        value["true_revise"] += scale * p * (gold == claimed == "revise")
                        value["false_action"] += scale * p * (claimed != "withhold" and gold != claimed)
                value["net"] = value["true_retain"] + value["true_revise"] - value["false_action"] - value["cost"]
                if method == "original":
                    assert all(abs(initial["replay"][inventory][name][k]-v) < 1e-9 for k, v in value.items())
                compare[method] = dict(value)
            controls[inventory][name] = compare
    return {"scope": "Exact routed reweighting with fixed actors. Ungated uses the same responses without exact quote "
                     "admission. The semantic veto uses authored labels to reject admitted errors without restoring "
                     "missing reads. Perfect replaces all reads with authored labels.",
            "source_sha256": {p.name: sha256(p.read_bytes()).hexdigest() for p in (ARTIFACT, TRANSFER)},
            "replay": controls}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
