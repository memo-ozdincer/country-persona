"""Verify the sampled update against finite differences on a single training menu."""
import json
from itertools import product

import numpy as np

import sampled_team as replay


def gradient(scene, weights, baseline):
    _, earlier, third = scene["open"]
    later = scene["adaptive"]
    zero = np.zeros_like(weights)

    def enumerate_actions(features):
        p = replay.old.softmax(features @ weights)
        centers = p.cumsum() - p / 2
        for action, uniform in enumerate(centers):
            realized, score = replay.draw(features[None, :, :], weights, np.array([uniform]))
            assert realized[0] == action
            yield action, p[action], score[0]

    for (b, pb, sb), (c, pc, sc), mask in product(
            enumerate_actions(earlier), enumerate_actions(third), range(8)):
        view = scene["observe"][b, mask]
        for a, pa, sa in enumerate_actions(later[view]):
            reward = scene["returns"][b, c, mask, a]
            zero += pb * pc * pa * scene["mask_probabilities"][mask] * (reward - baseline) * (sa + sb + sc)
    return zero


def run():
    scene, = replay.receipt.cases(replay.old.TRAIN_SEED, 1)
    weights = np.array([.11, .17, .23])
    eps = 1e-5
    finite = np.array([(replay.receipt.expected(scene, weights + eps * axis)[0] -
                        replay.receipt.expected(scene, weights - eps * axis)[0]) / (2 * eps)
                       for axis in np.eye(len(weights))])
    exact = replay.receipt.expected(scene, weights)[1]
    errors = {str(baseline): float(np.max(np.abs(gradient(scene, weights, baseline) - finite)))
              for baseline in (0., 9., 25.)}
    assert max(errors.values()) < 1e-8
    assert np.allclose(finite, exact, atol=1e-8, rtol=0)
    control = replay.receipt.PARENT / "delivery-aware/results.json"
    return {"absolute_error_against_finite_difference": errors, "open_exact_control_sha256": replay.old.DIGEST(control)}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
