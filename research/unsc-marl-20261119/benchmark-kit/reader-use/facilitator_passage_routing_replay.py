"""Recompute routing outcomes with mechanically verified message admission."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
from unittest.mock import patch

import numpy as np

import facilitator_measured_channel_fit as trained
import facilitator_passage_routing as study

fit, D = trained.fit, trained.D


def record(docket, docs):
    packet, cards = study.sources()[docket]
    blocks = []
    for c, card in enumerate(cards, 1):
        found = next((f"{docket}/{q}/{c}" for q in (0, c, *(x for x in range(1, 4) if x != c))
                      if docs[f"{docket}/{q}/{c}"]["delivery"]), None)
        if found is None:
            continue
        evidence = docs[found]["evidence_emitted"]
        assert set(evidence) == {"1", "2", "3"} and all(x in card["source"] for x in evidence.values())
        speaker = packet["cards"][c - 1]["speaker"]
        blocks.append({"source_slot": c, "speaker": speaker, "actual_reply": found, "verbatim_passages": evidence})
    return {"authority_anchor": packet["public"], "source_sections": blocks,
            "assembly": "Combine successful outputs from distinct test calls as a record assembly demonstration."}


def run(reply, weights):
    result = {}
    for docket, matrix in reply["matrices"].items():
        packet, _ = study.sources()[docket]
        authored = trained.rubric.ceilings(packet["criteria"])
        metrics = {name: np.array([[0, *(reply["records"][f"{docket}/{q}/{c}"][name] for c in range(1, 4))]
                                  for q in range(4)]) for name in ("input_tokens", "output_tokens")}
        risk = {"observed": np.asarray(matrix), "perfect": fit.PERFECT}
        measures = {}
        for scope, channel in risk.items():
            with patch.object(trained.rubric, "ceilings", lambda _: authored):
                report = trained.evaluate(weights, channel)
            for label, rows in report["policies"].items():
                prior = fit.ROUTE.TEST_PRIORS[label]
                opener, opening = fit.context(np.asarray(authored), prior)
                quiet = rows["exact_held_independent"]["net"]
                for key, val in rows.items():
                    q, r = map(np.asarray, val.pop("policy"))
                    mass = np.einsum("rbm,mt,rbtc->tc", opening, fit.heard(D.one_hot(q)), D.one_hot(r))
                    val["net_advantage_over_hindsight_no_request"] = val["net"] - quiet
                    val["expected_author_calls"] = float(mass[:, 1:].sum())
                    val["request_by_opening"] = q.tolist()
                    if scope == "observed":
                        for name, table in metrics.items():
                            val["expected_" + name] = float((mass * table).sum())
                    if scope == "observed" and key == "ideal_fit":
                        erased = fit.measure((q, r), opener, opening, prior, np.asarray(authored),
                                             np.broadcast_to(channel[0], channel.shape))
                        val["net_with_label_routing_but_no_question_at_writer"] = erased["net"]
            report.pop("one_cell_flip_advantage_over_fixed_measured_no_request")
            measures[scope] = report
        result[docket] = {"assembly_example": record(docket, reply["records"]), "measures": measures}
    return result


if __name__ == "__main__":
    argparse.ArgumentParser(description=__doc__).parse_args()
    reply = study.EVIDENCE / "admission.json"
    fitted = study.HERE / "facilitator-measured-channel-evidence/fits.json"
    print(json.dumps({"results": run(trained.read(reply), trained.read(fitted)),
                      "sha256": {str(p.relative_to(study.HERE)): sha256(p.read_bytes()).hexdigest()
                                 for p in (reply, fitted)}}, ensure_ascii=False, indent=2))
