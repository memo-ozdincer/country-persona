"""Price the generated-message channel and its targeted checks."""
import argparse
from collections import Counter
import json
from pathlib import Path

import numpy as np

import routing_climate_language_effects as effects
import routing_climate_language_gate as gate

channel, read, digest = gate.channel, gate.read, gate.digest
transfer = channel.transfer


def evaluate(path):
    final = read(path)
    notes, _ = gate.writer.capture(gate.BASE)
    names = [row["id"] for row in transfer.task()["optional_sources"]]
    lengths = np.asarray([0, *(len(notes[f"note-{field}"]["output"].split()) for field in names)])
    per_receipt = Counter(int(label.removeprefix("visible-")) for _, label, _, _, _ in gate.cases())
    calls = np.asarray([4 * per_receipt[m] for m in range(8)])
    groups = read(channel.PLAN)["plans"]
    priors, _, _ = transfer.original.selections()
    out = {}
    for name, prior in priors.items():
        result = {}
        for tag, plan in groups.items():
            receipts, attempted_words, fees = effects.cost_and_receipts(plan, prior, lengths)
            result[tag] = {"attempted_note_words": attempted_words,
                           "expected_gate_judgments": float(receipts @ calls), "route_fees": fees}
        controls = {}
        for tag in ("independent", "scripted"):
            extra = result["learned"]["expected_gate_judgments"] - result[tag]["expected_gate_judgments"]
            gain = final["score"]["results"]["release"][name]["learned_gains"][tag]
            controls[tag] = {"unpriced_gain": gain, "extra_checks": extra,
                             "positive_break_even_points_per_check": gain / extra if extra > 1e-9 and gain > 0 else None}
        out[name] = {"plans": result, "comparative_costs": controls}
    return {"scope": "Counterfactual per-episode costs with the actual trimmed note word lengths and the three "
                     "targeted scope checks. Use the same judge rule for all routes. Writer and query token "
                     "budgets are counted elsewhere. Break-even units are rubric points, not model prices.",
            "gate_score_sha256": digest(path), "calls_by_receipt": calls.tolist(), "priors": out}


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("gate_scores", type=Path)
    print(json.dumps(evaluate(cli.parse_args().gate_scores), indent=2))
