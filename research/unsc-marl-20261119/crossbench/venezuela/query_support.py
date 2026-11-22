"""Audit activation and observation-limited headroom on the Venezuela replay."""
from collections import Counter, defaultdict
import json
from pathlib import Path
from unittest.mock import patch

import query_deferral as experiment

gate = experiment.gate


def support(results):
    with patch.object(gate, "paired", new=experiment.paired):
        panels = gate.archived(list(gate.transfer.cases()))
    groups = defaultdict(list)
    for regime, rows in panels.items():
        for case, obs, now, later in rows:
            if obs is not None:
                groups[obs].append((regime, case, now, later))
    diagnostics = {}
    for view, rows in sorted(groups.items()):
        pattern = "".join("1" if b else "0" for b in view)
        changes = Counter()
        for regime, case, now, later in rows:
            changes[regime, case, str(int(later[0])-int(now[0]))] += 1
        diagnostics[pattern] = {
            "features": dict(zip(gate.FEATURES, view, strict=True)),
            "learned_defers": not gate.choose(view, results["rules"]),
            "effect_of_deferring": gate.router.sp.flatten(changes),
            "any_rescue": any(later[0] and not now[0] for _, _, now, later in rows),
            "any_regression": any(now[0] and not later[0] for _, _, now, later in rows),
        }
    # This table uses the evaluation data to choose only safe exact-observation
    # overrides. It is an in-sample upper bound under individual protection.
    safe = {view for view, rows in groups.items() if
            all(not now[0] or later[0] for _, _, now, later in rows) and
            any(later[0] and not now[0] for _, _, now, later in rows)}
    return {
        "scope": "In-sample exact-observation ceiling for deferring once without losing any certificate delivered by the fixed query schedule. One shared table across all Venezuela conditions.",
        "patterns": diagnostics,
        "safe_certificate_table": {condition: gate.score(rows, lambda view: view not in safe)
                                   for condition, rows in panels.items()},
    }


if __name__ == "__main__":
    archive = Path(__file__).parent/"evidence/query-deferral/results.json"
    print(json.dumps(support(json.loads(archive.read_text())), indent=2))
