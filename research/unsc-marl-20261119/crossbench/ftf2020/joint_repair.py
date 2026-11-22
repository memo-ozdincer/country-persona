"""Audit and repair a coordination plateau with paired local policy edits."""
from hashlib import sha256
from itertools import product
import json
from pathlib import Path

import numpy as np

import corroboration_receiver as receiver

HERE = receiver.HERE


def neighbors(sender, reply):
    for focus, (roster, signal) in product(range(4), product(range(6), range(2))):
        moved = sender.copy()
        adapted = reply.copy()
        moved[focus] = 1 - moved[focus]
        pair = receiver.transfer.routing.PAIR[roster]
        adapted[roster, signal] = int(pair.sum()) - adapted[roster, signal]
        yield (moved, adapted), {"requester_focus": focus, "responder_inventory": roster, "observed_signal": signal}


def run():
    calibration = receiver.transfer.Calibration()
    fit_path = HERE / "joint-fit-results.json"
    fitted = receiver.case.read(fit_path)
    registered = receiver.case.read(HERE / "corroboration-records.json")
    bare = np.asarray(registered["bare_scores"])
    gains = np.asarray(registered["joint_scores"]) - bare[:, None]
    requester, responder = map(np.asarray, fitted["policies"]["learned"])
    prior = calibration.design_prior
    exact = receiver.bound(prior, gains, bare, calibration)["prior_informed_interactive"]

    def score(sender, response):
        return receiver.utility(sender, response, prior, gains, bare, calibration)

    def unilateral(sender, response):
        sender_best = max(score(request, response) for request in receiver.transfer.routing.REQUESTS)
        response_best = receiver.policy(receiver.known_probability(sender, calibration.question_loss), prior, gains)
        return {"best_sender_only": sender_best, "best_responder_only": score(sender, response_best)}

    initial = score(requester, responder)
    assert np.isclose(initial, fitted["outcomes"]["design_mixture"]["learned"])
    before = unilateral(requester, responder)
    assert all(np.isclose(gain, initial) for gain in before.values())
    history = []
    current = (requester, responder)
    while True:
        chosen, change = max(neighbors(*current), key=lambda pair: score(*pair[0]))
        value = score(*chosen)
        if value < score(*current) + 1e-10:
            break
        history.append({**change, "before": score(*current), "after": value,
                        "sender": chosen[0].tolist(), "responder": chosen[1].tolist()})
        current = chosen
    assert score(*current) <= exact + 1e-10

    evaluations = {}
    for name, dist in {"design_mixture": prior, **calibration.priors}.items():
        new = receiver.utility(*current, dist, gains, bare, calibration)
        old = fitted["outcomes"][name]
        ceiling = old["prior_informed_interactive"]
        assert new <= ceiling + 1e-9
        evaluations[name] = {"post_repair": new, "pre_repair": old["learned"],
                             "design_exact": old["development_exact"], "informed_exact": ceiling,
                             "silent": old["blind_silent"]}
    return {"scope": "One fit followed by exact design-prior search. A repair simultaneously changes one local "
                     "requester action and one responder action. The move is accepted only if design reward strictly increases. "
                     "Neither the original fit nor the repair selects on the six unselected evaluation priors.",
            "code_sha256": sha256(Path(__file__).read_bytes()).hexdigest(), "fit_sha256": sha256(fit_path.read_bytes()).hexdigest(),
            "initial_unilateral_bounds": before, "initial_score": initial, "design_ceiling": exact,
            "accepted_paired_moves": history, "final_unilateral_bounds": unilateral(*current),
            "final_score": score(*current), "final_sender": current[0].tolist(), "final_responder": current[1].tolist(),
            "evaluations": evaluations}


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, indent=2))
