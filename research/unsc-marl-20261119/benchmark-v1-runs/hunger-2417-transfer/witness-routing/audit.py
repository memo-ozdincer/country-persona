"""Audit witness decisions, visible support and independently enumerated optima."""
from itertools import product
import json

from select_witness import decode, key, read, registry


def audit():
    result = read("results.json")
    registered = registry()
    historical = {}
    guards = 0
    terms = {}
    for row in result["grades"].values():
        card = json.loads(row["request"]["messages"][1]["content"])
        context = registered.get(key(card))
        reply_kind, status = decode(row["reply"])
        verdict = row["verdict"]
        assert verdict["admitted"] == bool(context and context == reply_kind and status == "linked")
        if context is None:
            assert not verdict["admitted"]
            guards += 1
        if row["cohort"] == "historical":
            historical[tuple(row["pair"]), row["order"]] = key(card)
            terms[row["order"]] = terms.get(row["order"], 0) + int(verdict["admitted"])
            assert row["screened"] == row["source_only"] + 18 * verdict["admitted"]
        else:
            assert "record" not in row and "screened" not in row
    for pair in {pair for pair, _ in historical}:
        assert historical[pair, "canonical"] == historical[pair, "reversed"]
    assert len(historical) == 12
    assert guards == 12
    assert result["reject_mutations"] == 42

    bound_count = 0
    for variant in ("canonical/screened", "reversed/screened", "canonical/authored"):
        table = result["tables"][variant]
        for row in result["evaluation"][variant]["rows"]:
            q0, q1, price, mass = row["setting"]
            for arm, tags in (("arrival_only", [1, 1, 1]), ("peer", [1, 2, 3])):
                best = float("-inf")
                for send in product((0, 1), repeat=3):
                    for action in product((0, 1), repeat=max(tags)+1):
                        value = 0.
                        for i in range(3):
                            prob = q0 * send[i]
                            full = table[6+2*i+action[tags[i]]]
                            single = table[4+action[0]]
                            value += mass[i] * (prob*((1-q1)*table[1+i]+q1*full)
                                                +(1-prob)*((1-q1)*table[0]+q1*single)
                                                -price*send[i])
                        best = max(best, value)
                assert abs(row["arms"][f"oracle/{arm}"][0]-best) < 1e-7
                for name, scores in row["arms"].items():
                    if name.startswith("fit_") and name.endswith(f"/{arm}"):
                        assert scores[0] <= best + 1e-7
                bound_count += 1
    queries = 0
    for fit in result["fits"].values():
        total = 0
        table = result["tables"]["canonical/screened"]
        for batch in fit["train_trace"]:
            for i, value in zip(batch["indices"], batch["scores"], strict=True):
                assert table[i] == value
                total += 1
        assert total == 1024
        queries += total
    repaired = read("repair-results.json")
    assert len(repaired["repairs"]) == 3
    for ident, row in result["grades"].items():
        decision = repaired["decisions"][ident]
        if decision["registered"] is None:
            assert not decision["admitted"]
        if ident in repaired["repairs"]:
            assert row["verdict"]["status"] == "invalid_witnesses" and decision["admitted"]
    assert repaired["tables"]["canonical/authored"] == repaired["tables"]["canonical/screened"]
    assert repaired["tables"]["canonical/authored"] == repaired["tables"]["reversed/screened"]
    repaired_checks = 0
    for variant in ("canonical/screened", "reversed/screened"):
        rows = repaired["evaluation"][variant]["rows"]
        reference = result["evaluation"]["canonical/authored"]["rows"]
        for row, expected in zip(rows, reference, strict=True):
            assert row["setting"] == expected["setting"]
            for arm in ("arrival_only", "peer"):
                earned = row["arms"][f"fit_1024/{arm}"][0]
                assert earned == row["arms"][f"fixed_authored/{arm}"][0]
                assert earned == expected["arms"][f"oracle/{arm}"][0]
                repaired_checks += 1
    repaired_queries = sum(
        len(batch["indices"]) for fit in repaired["fits"].values() for batch in fit["train_trace"]
    )
    assert repaired_queries == 2048
    for fit in repaired["fits"].values():
        table = repaired["tables"]["canonical/screened"]
        for batch in fit["train_trace"]:
            assert batch["scores"] == [table[i] for i in batch["indices"]]
    return {"historical_admissions": terms, "unregistered_packets_rejected": guards,
            "tamper_checks": result["reject_mutations"], "oracle_settings_checked": bound_count,
            "strict_simulated_training_score_checks": queries,
            "repaired_held_optima_matched": repaired_checks,
            "repaired_simulated_training_score_checks": repaired_queries}


if __name__ == "__main__":
    print(json.dumps(audit(), indent=2))
