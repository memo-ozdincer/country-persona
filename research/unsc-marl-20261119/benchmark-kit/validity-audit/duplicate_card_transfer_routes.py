"""Replay the archived policy and exact controls under two inventory distributions."""
import json

import numpy as np

from duplicate_card_records import FIT
from duplicate_card_routes import PAYOFF, SIGNAL_COST, TEST, exact, play, summarize
from duplicate_card_transfer import CASE, SKEW
from source_record_run import digest


def run():
    old = json.loads(FIT.read_text())
    slots = list(json.loads(CASE.read_text())["cards"])
    table = np.asarray(old["learned_table"])
    signals, actions, _ = [x[0] for x in play(table[None], PAYOFF)]
    priors = {"uniform": TEST["all_inventories"], "skew": np.outer(*SKEW).flatten()}
    result = {}
    for prior_id, prior in priors.items():
        assert np.isclose(prior.sum(), 1.0)
        controls = exact(prior, PAYOFF, SIGNAL_COST)
        arms = {key: summarize(prior, bits, choices) for key, (_, bits, choices) in controls.items()}
        arms["learned"] = summarize(prior, signals, actions)
        assert arms["learned"]["net"] <= arms["optional"]["net"] + 1e-9
        result[prior_id] = arms
    assert result["uniform"]["learned"] == old["arms"]["all_inventories"]["learned"]
    return {"case_sha256": digest(CASE), "frozen_policy_sha256": digest(FIT), "slots": slots,
            "new_inventory_marginals": SKEW, "arms": result}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
