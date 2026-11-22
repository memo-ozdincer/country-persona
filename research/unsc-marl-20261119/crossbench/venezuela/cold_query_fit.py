"""Fit deferral explicitly for decisions with no previously cached peer receipt."""
import json
from unittest.mock import patch

import query_deferral as deferral

gate = deferral.gate
SEEDS = {"training": 929789, "validation": 182353, "holdout": 500137}
CACHED = gate.FEATURES.index("other_receipt_cached")


def cold(rows):
    return [row for row in rows if row[1] is not None and not row[1][CACHED]]


def evaluate():
    with patch.object(gate, "paired", new=deferral.paired), patch.object(gate, "SEEDS", new=SEEDS):
        train = gate.synthetic("training", (5, 6), 700, 2)
        dev = gate.synthetic("validation", (6,), 700, 3)
        rules, journal = gate.fit({k: cold(v) for k, v in train.items()}, {k: cold(v) for k, v in dev.items()})
        test = gate.synthetic("holdout", (7, 8), 460, 3)
        archived = gate.archived(list(gate.transfer.cases()))

    def decisions(panels):
        return {k: {
            "query": gate.score(rows, lambda _: True),
            "defer_once": gate.score(rows, lambda _: False),
            "cold_fit": gate.score(rows, lambda obs: obs[CACHED] or gate.choose(obs, rules)),
        } for k, rows in panels.items()}

    return {
        "scope": "Synthetic refit after diagnosing cold-receipt shift. Three new synthetic seeds. Venezuela is an exposed transfer diagnostic.",
        "seeds": SEEDS, "fit": journal, "rules": rules,
        "synthetic_holdout": decisions(test),
        "cold_only_subset": decisions({k: cold(v) for k, v in test.items()}),
        "venezuela_exposed": decisions(archived),
    }


if __name__ == "__main__":
    print(json.dumps(evaluate(), indent=2))
