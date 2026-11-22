"""Compare public-ledger and Qwen observations at a matched training budget."""
from pathlib import Path

import factor
import torch

base, E, HERE = factor.base, factor.E, factor.HERE
P = factor.P
ACT = factor.learn.ACTIONS


def run():
    torch.set_num_threads(1)
    roster, x, z, _ = base.observations()
    receipt = E.read(HERE/"ledger-features.json")
    public = receipt["features"]
    table = E.read(HERE/"reward-table.json")["paths"]
    old = E.read(HERE/"factor.json")
    n = len(roster["train"])
    sequence = [(split, row["id"]) for split in ("train", "held") for row in roster[split]]
    z_public = torch.tensor([public[split][key] for split,key in sequence], dtype=x.dtype)
    selected = [table[split][key] for split, key in sequence]
    truth = torch.tensor([ACT.index(item["truthful_action"]) for item in selected])
    sign_value = torch.tensor([row["reward"][act] for row, act in zip(selected, truth, strict=True)], dtype=x.dtype)
    pass_value = torch.tensor([row["reward"][P] for row in selected], dtype=x.dtype)
    # Distinct parameters for positive versus negative authenticated signs.
    type_column = z_public[:, -1:]
    centered = z_public[:, :-1]
    grouped = torch.cat((centered * type_column, centered * (1-type_column)), dim=1)
    margin = z.gather(1, truth[:, None]).squeeze(1) - z[:, P]
    weights, histories = {}, {}
    predictions = {}
    for name, observed, initial in (
        ("ledger_only", grouped, torch.zeros_like(margin)),
        ("ledger_qwen", torch.cat((x, grouped), dim=1), margin),
    ):
        w, trace = factor.fit(observed[:n], initial[:n], sign_value[:n], pass_value[:n])
        weights[name], histories[name] = w.tolist(), trace
        score = initial + observed @ w
        predictions[name] = torch.where(score > 0, truth, P)
    predictions["qwen_only"] = torch.where(margin + x @ torch.tensor(old["weights"], dtype=x.dtype) > 0, truth, P)
    predictions["exact"] = torch.where(sign_value > pass_value, truth, P)
    onehot = {name: torch.nn.functional.one_hot(v[n:], num_classes=3) for name,v in predictions.items()}
    evaluated = factor.learn.outcomes(roster["held"], onehot, table["held"])
    assert evaluated["summary"]["qwen_only"] == old["held"]["summary"]["learned_send"]
    assert evaluated["summary"]["exact"] == old["held"]["summary"]["exact"]
    assert all(v["false_sign"] == 0 for v in evaluated["summary"].values())
    files = (Path(__file__), HERE/"ledger-protocol.md", HERE/"ledger-features.json", HERE/"reward-table.json",
             HERE/"factor.json", base.CAPTURE/"vectors.npz")
    return {"held_role_menu_relabelings": receipt["held_role_menu_relabelings"],
            "updates_per_fit": base.STEPS, "qwen_updates": 0, "weights": weights, "traces": histories,
            "sha256": {p.name: base.digest(p) for p in files}, "held": evaluated}


if __name__ == "__main__":
    E.emit(run())
