"""Train with identical openings across paired changes in rubric complements."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
from unittest.mock import patch

import numpy as np

import facilitator_third_delivery_context as base
import facilitator_third_delivery_context_audit as audit

HERE = Path(__file__).resolve().parent
BASELINE = HERE / "facilitator-third-context-evidence/fit.json"
PRIOR = base.route.TEST_PRIORS["uniform"]


def training_contexts(training):
    contexts = {}
    for name, (public, _) in training.items():
        if "/" not in name:
            contexts[tuple(public)] = base.context(public, PRIOR)
            continue
        anchor = base.rubric(int(public[0]), public[[1, 2, 4]] - public[0])
        left, right, opening, features = base.context(anchor, PRIOR)
        features[:8] = (base.terminal(public) - public[0]) / 36.
        contexts[tuple(public)] = left, right, opening, features
    for name, (public, _) in training.items():
        if "/" not in name:
            continue
        weights, _, strength = name.split("/")
        peers = [p for label, (p, _) in training.items() if label.startswith(weights + "/") and
                 label.endswith("/" + strength)]
        assert len(peers) == 3
        expected = contexts[tuple(public)][-1][8:]
        assert all(np.array_equal(contexts[tuple(peer)][-1][8:], expected) for peer in peers)
    return contexts


def run():
    prior = json.loads(BASELINE.read_text())
    training, held = base.cases()
    contexts = training_contexts(training)
    with patch.object(base, "context", side_effect=lambda public, _: contexts[tuple(public)]):
        net, trace = base.train(training)
    old_net = audit.restored(prior["network"])
    results = base.evaluate(net, held, json.loads((base.THIS_EVIDENCE / "fit.json").read_text()))
    return {
        "scope": "Same initialization, optimization settings, reward profiles and held banks as the prior fit. "
                 "Use one singleton-based opening in each group of three synthetic complement placements. "
                 "Historical transfer uses the original public opening planner for both networks.",
        "updates": len(trace), "trace": trace,
        "train_contexts": {name: {"left": contexts[tuple(p)][0].tolist(), "right": contexts[tuple(p)][1].tolist()}
                           for name, (p, _) in training.items()},
        "network": {key: value.tolist() for key, value in net.state_dict().items()},
        "fixed_opening_contrast": {"previous": audit.rank_contrast(old_net), "paired": audit.rank_contrast(net)},
        "archived_transfer": results,
        "sha256": {path.name: sha256(path.read_bytes()).hexdigest() for path in (
            Path(__file__), Path(base.__file__), Path(audit.__file__), BASELINE)},
    }


if __name__ == "__main__":
    argparse.ArgumentParser(description=__doc__).parse_args()
    print(json.dumps(run(), indent=2, ensure_ascii=False))
