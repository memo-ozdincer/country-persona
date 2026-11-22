"""Compare equal-reward one-bit routing and named requests for a missing record."""
from hashlib import sha256
import json
from pathlib import Path
import socket

import numpy as np

import corroboration_receiver as receiver
import fit

HERE = receiver.HERE
BONUS = 28


def run():
    route = receiver.transfer.routing
    setup = receiver.transfer.Calibration()
    published_record = receiver.case.bank()
    assert published_record["keys"] == receiver.case.KEYS
    design = setup.design_prior
    initial, learned, learning_trace = fit.train(design)
    optimized = route.optimize(design)["policies"]["exact_interactive"]
    exact = [np.asarray(optimized[key]) for key in ("sender", "receiver")]
    pairs = np.asarray(receiver.case.PAIRS)
    possible = (np.arange(4)[:, None, None] == pairs[None, :, :]).any(axis=-1)

    def score_named(prior):
        available = float((possible * prior).sum())
        reach = (1 - setup.question_loss) * available
        completion = (1 - setup.reply_loss) * reach
        return {
            "request_fulfillment": completion,
            "net_completion_bonus": BONUS * completion - setup.question_fee - setup.reply_fee * reach,
            "physical_reply_only_ceiling": available * (1 - setup.reply_loss),
        }

    def score_bit(policy, prior):
        info = route.measure(prior, *policy)
        return {"request_fulfillment": info["probability_of_correct_backup_delivery"],
                "net_completion_bonus": info["net"] - 42}

    rows = {}
    for name, prior in {"design_mixture": design, **setup.priors}.items():
        upper = route.optimize(prior)["policies"]
        two = {
            "named": score_named(prior),
            "learned_one_bit": score_bit(learned, prior),
            "design_optimal_one_bit": score_bit(exact, prior),
            "prior_informed_silent": score_bit(
                [np.asarray(upper["silent_pair"][k]) for k in ("sender", "receiver")], prior),
            "prior_informed_one_bit": score_bit(
                [np.asarray(upper["exact_interactive"][k]) for k in ("sender", "receiver")], prior),
        }
        assert two["prior_informed_one_bit"]["net_completion_bonus"] + 1e-9 >= max(
            row["net_completion_bonus"] for mode, row in two.items() if mode != "named")
        rows[name] = two
    return {"scope": "Condition on a conjunctive request already having one of its two required cards protected "
                     "at the requester. The hidden focus is the other required card. Enumerate every possible focus "
                     "and responder roster in each synthetic prior. Train one pair from scratch against completing "
                     "that request, using the same one-bit and loss model as the existing experiment. "
                     "The exact symbolic control uses the same development prior. Named requests have a larger "
                     "alphabet and a reply only after delivery and local match. The cost model does not price bandwidth. "
                     "If neither requested card is protected, this one-reply protocol cannot complete the pair.",
            "host": socket.gethostname(), "device": "CPU", "optimizer_steps": fit.UPDATES, "seed": fit.SEED,
            "code_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
            "reused_fit_sha256": sha256(Path(fit.__file__).read_bytes()).hexdigest(),
            "initial_policy": [x.tolist() for x in initial], "learned": [x.tolist() for x in learned],
            "exact": [x.tolist() for x in exact], "training_trace": learning_trace, "outcomes": rows}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
