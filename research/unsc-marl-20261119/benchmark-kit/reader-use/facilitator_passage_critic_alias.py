"""Bound shared request policies when two reward banks have identical public inputs."""
import json

import numpy as np

import facilitator_passage_responder_critic as critic

NAMES = ("unama", "emergency")


def run():
    cases = critic.joint.historic.read(critic.EVIDENCE / "results.json")["score_bank_cases"]
    archived = critic.fit.OLD.base.cases()[1]
    public, alternative = [archived[name][0] for name in NAMES]
    assert np.array_equal(public, alternative)
    assert not np.array_equal(*(archived[name][1] for name in NAMES))
    maps = critic.fit.MAPS
    result = {}
    for law in critic.fit.live.PRIORS:
        first, second = [cases[name][law] for name in NAMES]
        assert first["receipt_visits"] == second["receipt_visits"]
        assert first["declared_values"] == second["declared_values"]
        visits = np.asarray(first["receipt_visits"])
        gains = np.asarray([row["measured_values"] for row in (first, second)])
        value = (gains[:, np.arange(8), maps] * visits).sum(-1)
        optimum = value.max(-1)
        regret = optimum[:, None] - value
        assert np.allclose(optimum, [r["policies"]["hindsight"]["gain_over_fixed_team_silence"]
                                     for r in (first, second)], rtol=0, atol=1e-10)

        def summary(chair):
            index, = np.flatnonzero(np.all(maps == chair, axis=1))
            return {"questions": maps[index].tolist(), "gains": dict(zip(NAMES, value[:, index].tolist())),
                    "regret": dict(zip(NAMES, regret[:, index].tolist())),
                    "requests": float(visits @ (maps[index] != 0))}

        result[law] = {
            "reachable_receipts": int(np.count_nonzero(visits > 1e-12)),
            "declared": summary(first["policies"]["declared"]["questions"]),
            "highest_worst_case_gain": summary(maps[value.min(0).argmax()]),
            "lowest_worst_case_regret": summary(maps[regret.max(0).argmin()]),
            "highest_equal_weight_mean": summary(maps[value.mean(0).argmax()]),
            "case_specific_optimums": dict(zip(NAMES, optimum.tolist())),
        }
    return {"public_score_vector": public.tolist(), "scored_vectors": {name: archived[name][1].tolist()
                                                                         for name in NAMES},
            "legal_maps_per_law": len(maps), "results": result}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
