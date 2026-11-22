"""Test a constrained reward-trained action head and its dependence on Qwen."""
from hashlib import sha256
import json

import torch

from duplicate_card_language_rl import (
    ACTIONS, DTYPE, LR, STEPS, decision_table, fit, probabilities, read_base, return_by_world, simulate,
)
from duplicate_card_outcome_policy import PRIORS, archived_profiles
from duplicate_card_transport import FAULTS

FULL = ACTIONS / "reward-fit.json"


def run():
    torch.set_num_threads(1)
    base = read_base()
    zeros = tuple(torch.zeros_like(t) for t in base["venezuela"])
    from_model, report_model = fit(base["venezuela"], shared_by_peer=True)
    from_zero, report_zero = fit(zeros, shared_by_peer=True)
    full = json.loads(FULL.read_text())
    assert full["archived_actions_sha256"] == sha256((ACTIONS / "actions.jsonl").read_bytes()).hexdigest()
    archived, hashes = archived_profiles()
    values = {"venezuela": archived["venezuela_original_release"], "dprk": archived["dprk_reordered_hybrid"]}
    tests = {}
    for case, logits in base.items():
        views = {"frozen_qwen": probabilities(logits, zeros),
                 "qwen_small": probabilities(logits, from_model),
                 "zero_small": probabilities(zeros, from_zero),
                 "isolated_small": probabilities(zeros, from_model)}
        tables = {mode: decision_table(p) for mode, p in views.items()}
        by_prior = {}
        for name, prior in PRIORS.items():
            by_prior[name] = {}
            for condition in ("none", "both_10", "both_25"):
                rates = FAULTS[condition]
                matrix = values[case]
                scores = {}
                for mode, p in views.items():
                    expected = torch.as_tensor(prior, dtype=DTYPE) @ return_by_world(*p, rates, 14.)
                    greedy = simulate(tables[mode], prior, matrix, *rates)["writer"]["buffered"]
                    scores[mode] = {"greedy_net": greedy["net"], "stochastic_net": float(expected) + matrix[0, 0]}
                previous = full["cases"][case]["evaluation"][name][condition]
                by_prior[name][condition] = {"exact_silent": previous["exact_silent"],
                                            "typed": previous["typed"],
                                            "full_residual": previous["qwen_residual"], "arms": scores}
        tests[case] = {"greedy_tables": {k: t.tolist() for k, t in tables.items()}, "priors": by_prior}

    return {"scope": "Follow-up on the exposed two-docket probe. Only sixteen local action biases "
                     "are fitted using the synthetic team objective. DPRK logits remain excluded from fitting.",
            "steps": STEPS, "learning_rate": LR, "parameter_count": sum(x.numel() for x in from_model),
            "training": {"qwen_small": {**report_model, "corrections": [x.tolist() for x in from_model]},
                         "zero_small": {**report_zero, "corrections": [x.tolist() for x in from_zero]}},
            "full_fit_sha256": sha256(FULL.read_bytes()).hexdigest(), "score_hashes": hashes, "tests": tests}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
