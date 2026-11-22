"""Test a source-local likelihood model under the same learned cross-play reward."""
import json
from pathlib import Path
from unittest.mock import patch

import numpy as np
import torch

import routing
import train_calibrator as baseline

HERE = routing.HERE


def train(features, rewards):
    torch.set_num_threads(1)
    torch.manual_seed(baseline.SEED)
    dt = baseline.DT
    cover = torch.nn.Parameter(.02 * torch.randn(6, 4, dtype=dt))
    likelihood = torch.nn.Parameter(.02 * torch.randn(2, 2, dtype=dt))
    optimizer = torch.optim.Adam([cover, likelihood], lr=.035)
    observations = torch.as_tensor(features[:, :4].reshape(16, 6, 2, 4), dtype=torch.long)
    query = torch.arange(2)[None, None, :, None]
    allowed = torch.as_tensor(routing.OPTIONS[None, :, None, :])
    target = torch.as_tensor(rewards, dtype=dt)
    history = []
    for step in range(baseline.STEPS + 1):
        score = (cover[None, :, None, :] + likelihood[observations, query]).masked_fill(~allowed, -torch.inf)
        expected = (score.softmax(dim=-1) * target).sum()
        history.append(float(expected.detach()))
        if step == 0:
            initial = score.detach().argmax(dim=-1).numpy()
        if step == baseline.STEPS:
            break
        optimizer.zero_grad()
        (-expected).backward()
        assert torch.isfinite(cover.grad).all() and torch.isfinite(likelihood.grad).all()
        optimizer.step()
    return initial, score.detach().argmax(dim=-1).numpy(), history


def run():
    with patch.object(baseline, "train", train):
        result = baseline.run()
    result["scope"] += " This variant adds one source-specific background score and a shared likelihood for the "                        "source's own probe result and the current request bit."
    result["variant_code_sha256"] = routing.digest(Path(__file__))
    control_path = HERE / "learned-calibration-results.json"
    control = json.loads(control_path.read_text())
    assert result["calibration_sha256"] == control["calibration_sha256"]
    result["control_sha256"] = routing.digest(control_path)
    result["excluded_margins_by_prior"] = {}
    for prior in result["evaluations"]["0000"]["learned"]:
        records = [value for value in result["evaluations"].values() if value["split"] == "excluded"]
        keys = [key for key, value in result["evaluations"].items() if value["split"] == "excluded"]
        mean = {metric: float(np.mean([row[metric][prior] for row in records]))
                for metric in ("learned", "same_probe_exact_decoding")}
        original = float(np.mean([control["evaluations"][key]["learned"][prior] for key in keys]))
        result["excluded_margins_by_prior"][prior] = {**mean, "unfactored_learned": original,
                                                     "gap_to_exact": mean["learned"] - mean["same_probe_exact_decoding"]}
    return result


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, indent=2))
