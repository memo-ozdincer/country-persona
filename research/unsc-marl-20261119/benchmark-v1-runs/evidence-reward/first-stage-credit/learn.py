"""Matched frozen-feature training with decision and final-record rewards."""
from collections import Counter
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
SIGNED = HERE.parent.parent / "language-signed-reply"
sys.path.insert(0, str(SIGNED))
import fit as base
import torch

E = base.E
ACTIONS = base.cases.DEC


def outcomes(rows, logits, table):
    results = {}
    metrics = {}
    for name, pred in logits.items():
        tally = Counter()
        for i, row in enumerate(rows):
            key = row["id"]
            info = table[key]
            action = ACTIONS[int(pred[i].argmax())]
            assessed = row["audit"][action]
            released, fee, asks = info["guarded_outcome"][action]
            correct_followup_context = (info["live_followup_context"] and assessed["new_proof"]
                                        and action == info["truthful_action"])
            details = {"action": action, "false_sign": not assessed["truthful"],
                       "new_proof": assessed["new_proof"], "live_followup_reached_if_delivered": correct_followup_context,
                       "expected_released_70": released, "expected_send_and_followup_cost": fee,
                       "expected_followups": asks, "net": released/70 - fee}
            results.setdefault(key, {})[name] = details
            for k, val in details.items():
                if k != "action":
                    tally[k] += val
            tally["signed_replies"] += action != "P"
        metrics[name] = dict(tally)
    return {"rows": results, "summary": metrics}


def run():
    torch.set_num_threads(1)
    files = E.read(base.CAPTURE/"complete.json")
    assert all(base.digest(base.CAPTURE / name) == sha for name, sha in files.items())
    roster, x, z, old_u = base.observations()
    table = E.read(HERE/"reward-table.json")["paths"]
    assert all(not any("unreviewed" in b for b in item["review"].values()) for item in table["held"].values())
    n = len(roster["train"])
    assert n == 144 and len(roster["held"]) == 44
    new_u = torch.tensor([table[split][row["id"]]["reward"] for split in ("train", "held")
                          for row in roster[split]], dtype=base.DTYPE)
    same_argmax = old_u.argmax(-1) == new_u.argmax(-1)
    assert same_argmax.all()
    old_w, old_trace = base.train(x[:n], z[:n], old_u[:n])
    new_w, new_trace = base.train(x[:n], z[:n], new_u[:n])
    exact = torch.nn.functional.one_hot(new_u.argmax(-1), num_classes=3)
    report = outcomes(roster["held"], {"frozen": z[n:], "decision_fit": z[n:] + x[n:] @ old_w,
                      "record_fit": z[n:] + x[n:] @ new_w, "exact": exact[n:]}, table["held"])
    archived = E.read(SIGNED/"results.json")["evaluation"]["held"]["rows"]
    for key, items in report["rows"].items():
        assert items["decision_fit"]["action"] == archived[key]["arms"]["residual"]["selected"]
    pins = (Path(__file__), HERE/"protocol.md", HERE/"reward-table.json", SIGNED/"results.json",
            SIGNED/"fit.py", base.CAPTURE/"vectors.npz")
    return {"updates_per_fit": base.STEPS, "qwen_updates": 0, "exact_best_actions_fit_excluded_unchanged": len(roster["held"]),
            "exact_best_actions_synthetic_unchanged": n,
            "weights": {"decision": old_w.tolist(), "record": new_w.tolist()},
            "trace": {"decision": old_trace, "record": new_trace}, "held": report,
            "sha256": {str(path.relative_to(SIGNED.parent)): base.digest(path) for path in pins}}


if __name__ == "__main__":
    E.emit(run())
