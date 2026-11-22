"""Decompose the effect of generated payloads under the frozen routes."""
import argparse
import json
from pathlib import Path

import numpy as np

import routing_climate_language_channel as language

transfer, read, digest = language.transfer, language.read, language.digest
route = transfer.route


def cost_and_receipts(group, prior, lengths):
    distribution = np.zeros(8)
    tokens = fees = 0.
    for packed, swap, weight in group:
        policy = transfer.base.space.as_policy(packed)
        ask, send, reply = policy
        active = prior.T if swap else prior
        replay = route.evaluate(policy, active, np.zeros(8), route.TRAIN_LOSS)
        distribution += weight * np.asarray(replay["receipt_distribution"])
        fees -= weight * replay["net"]
        first = lengths[send][:, None]
        arrives = lengths[reply[:, ask].T]
        missing = lengths[reply[:, 0]][None, :]
        tokens += weight * np.sum(active * (first + (1 - route.TRAIN_LOSS) * arrives + route.TRAIN_LOSS * missing))
    return distribution, float(tokens), float(fees)


def compare(path):
    measured = read(path)
    assert measured["verified_source_baseline_sha256"] == digest(language.WRITING_BASE)
    fresh = measured["arms"]["visible"]
    approved = read(language.WRITING_BASE)["arms"]["visible"]
    plans = read(language.PLAN)["plans"]
    priors, _, _ = transfer.original.selections()
    fields = [source["id"] for source in transfer.task()["optional_sources"]]
    lengths = np.asarray([0, *(measured["notes"][f"note-{field}"]["tokens"] for field in fields)])
    result = {}
    for prior_name, p in priors.items():
        rows = {}
        for plan_name, group in plans.items():
            distribution, attempted_tokens, fees = cost_and_receipts(group, p, lengths)
            writer_change = {}
            for tag in ("raw", "release"):
                old, new = approved["results"][tag][prior_name], fresh["results"][tag][prior_name]
                credits = np.asarray(fresh[tag]) - np.asarray(approved[tag])
                delta = new["nets"][plan_name] - old["nets"][plan_name]
                assert abs(delta - float(distribution @ credits)) < 1e-8
                assert abs(new["nets"][plan_name] - (float(distribution @ fresh[tag]) - fees)) < 1e-8
                writer_change[tag] = {"old_net": old["nets"][plan_name], "new_net": new["nets"][plan_name],
                                      "change": delta, "per_receipt": (distribution * credits).tolist()}
            rows[plan_name] = {"expected_attempted_note_tokens": attempted_tokens, "retained_fees": fees,
                               "receipt_distribution": distribution.tolist(), **writer_change}
        result[prior_name] = rows
    return {"scope": "Identical frozen actions and message fees with alternate text payloads. Expected note tokens "
                     "use actual tokenizer output lengths, price attempted sends even when lost, and exclude "
                     "writer tokens and any query text. Cached field notes are shared across methods.",
            "score_sha256": digest(path), "baseline_sha256": digest(language.WRITING_BASE), "priors": result}


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("scores", type=Path)
    print(json.dumps(compare(cli.parse_args().scores), indent=2))
