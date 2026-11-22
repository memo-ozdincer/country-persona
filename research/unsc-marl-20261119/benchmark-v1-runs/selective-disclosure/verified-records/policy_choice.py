"""Use recipient return forecasts to decide when to apply the learned correction."""
from hashlib import sha256
import json
from pathlib import Path
from statistics import mean
from unittest.mock import patch

import numpy as np
import torch

import replay as prior

HERE = Path(__file__).resolve().parent
s = prior.s


def run():
    torch.set_num_threads(1)
    bank = s.read(HERE/"results.json")
    registry = s.read(s.original.REGISTRY)
    original = torch.tensor(s.read(s.FIT)["weights"], dtype=torch.float64)
    open_w = np.asarray(s.read(HERE.parent/"joint-opener.json")["weights"])
    rank = np.asarray(s.read(HERE.parent/"ranking.json")["coef"])
    value = np.asarray(s.read(HERE.parent/"recipient.json")["weights"])
    model = s.read(HERE.parent/"history-prior.json")["cases"]
    held = {r["draw"]: r for r in registry["accepted"] if r["draw"] in registry["partition"]["reserved"]}

    def grid_of(name):
        if name in ("mali", "myanmar"):
            return s.shared.Grid(name)
        with patch.dict(s.shared.FIXTURES, {"policy-choice": s.original.fixture(held[int(name.split("-")[1])])}):
            return s.shared.Grid("policy-choice")

    def forecast(grid, balanced):
        data = s.shared.Experiment(grid, balanced)
        for i, role in enumerate(data.roles):
            if role == 2:
                data.mask[i, 1:] = False
        start = data.probabilities(original).numpy()
        response = prior.opener.basis(data, data.prior, start)
        opening = prior.opener.choose(data, start, response, open_w, s.base.FEE, "joint-fitted")
        forecasts = prior.recipient.aggregate(data, opening)
        scores = prior.ranking.measure(data, opening, forecasts, rank, value)
        return forecasts, scores["rank-fit"][1]["net"]-scores["fixed"][1]["net"]

    results = {}
    for case, previous in bank["cases"].items():
        grid = grid_of(case)
        (one, gain_bal), (two, gain_uni) = [forecast(grid, balanced) for balanced in (True, False)]
        dist = prior.history.mass_distribution((one,two), True)
        post, mass = prior.history.likelihoods(dist)[0][32]
        use_rank = post*gain_bal + (1-post)*gain_uni > 1e-12
        chance = dict(zip(prior.MODES, mass[use_rank].sum(0).tolist(), strict=True))
        conditional = {}
        for mode, probability in chance.items():
            rows = previous["regimes"][mode]["metrics"]
            values = {k: rows["fixed"][k]+probability*(rows["rank-fit"][k]-rows["fixed"][k])
                      for k in rows["fixed"]}
            ref = model[case]["history"]["own+messages"]["horizons"]["32"]["policies"]["model-candidate"][mode]
            assert abs(values["net"]-ref) < 1e-9
            conditional[mode] = values
        averages = {k: mean(arm[k] for arm in conditional.values()) for k in conditional["balanced"]}
        results[case] = {"probability_rank": chance, "equal_mixture": averages, "conditional": conditional}
    summary = {}
    for group, keys in (("reserved", [k for k in results if k.startswith("space-")]),
                        ("transfer", ["mali","myanmar"])):
        summary[group] = dict(bank["macro"][group],
                              **{"payoff-selector-32": {key: mean(results[case]["equal_mixture"][key] for case in keys)
                                                       for key in results[keys[0]]["equal_mixture"]}})
    pins = (HERE/"choice-protocol.md", HERE/"results.json", HERE.parent/"history-prior.json")
    return dict(macro=summary, cases=results, pins={p.name:sha256(p.read_bytes()).hexdigest() for p in pins})


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, indent=2))
