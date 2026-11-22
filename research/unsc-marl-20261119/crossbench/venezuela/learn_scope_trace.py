"""Replay the held-out certificate gain with the executed message ledger."""
import json
from pathlib import Path
from unittest.mock import patch

import learn_scope as fit


def trace(item, terms, decision, action):
    events, views = [], []

    def choose(obs):
        answer = decision(obs)
        views.append({"local_observation": dict(zip(fit.FEATURES, obs, strict=True)),
                      "disclose_scope": answer})
        return answer

    with patch.object(fit.selection.reuse, "singleton_enabled",
                      new=lambda: fit.selection.enabled(True, choose)):
        with fit.transfer.canonical.enabled(terms, "public", lambda: fit.episode.delay.enabled(
                lambda _: "immediate")):
            result = fit.transfer.router.play(item, fit.transfer.canonical.BASE, {}, events=events)
    return {"decision": views, "outcome": dict(zip(fit.METRICS[:6], result, strict=True)),
            "role_ledger": events, "arm": action}


def examples(results):
    seed = fit.SEEDS["holdout"]
    rows, terms = zip(*fit.episode.base.synth.worlds((7, 8), 500, 3, seed), strict=True)
    physical = fit.transfer.router.routing.refit.drop_returns(rows, seed+1)
    output = []
    policy = results["policy"]

    def select(obs):
        return fit.disclose(obs, policy)

    for index, (item, description) in enumerate(zip(
            fit.episode.transport.delivery(physical, seed+2, 0), terms, strict=True)):
        obs, original = fit.played(item, description, None, lambda _: True, "immediate")
        if obs is None or original[0] or select(obs):
            continue
        _, revised = fit.played(item, description, None, select, "immediate")
        if not revised[0]:
            continue
        before = trace(item, description, lambda _: True, "always_disclose")
        after = trace(item, description, select, "fitted")
        assert before["outcome"]["certificate"] is False and after["outcome"]["certificate"] is True
        assert before["decision"][0]["local_observation"] == after["decision"][0]["local_observation"]
        left, right = item[0][1]
        output.append({"row": index, "seed": seed, "ground_truth": "agreement" if left & right else "impasse",
                       "opened": fit.transfer.router.sp.opened(item[0][3], item[0][2]),
                       "options": description, "before": before, "after": after})
    assert len(output) == 1 and output[0]["ground_truth"] == "impasse"
    return output


if __name__ == "__main__":
    import sys

    results = json.loads(Path(sys.argv[1]).read_text())
    print(json.dumps(examples(results), indent=2))
