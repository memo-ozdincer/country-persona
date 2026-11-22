"""Replay fixed routing on paired scope checks, without a downstream writer."""
import argparse
from collections import defaultdict
from hashlib import sha256
from itertools import combinations, product
import json
from pathlib import Path
from unittest.mock import patch

import facilitator_witness_contrast as study
import facilitator_receipt_ceiling as ceiling
import facilitator_receipt_search as exact

record = ceiling.prior.record
MODES = ("literal", "direct", "compare_first", "compare_strip", "typed_compare", "oracle")


def observations(audit, key, truth, arm):
    if arm == "literal":
        return True, truth == "conflict"
    if arm == "oracle":
        return truth == "conflict", truth == "conflict"
    row = audit["checks"][f"{key}/{arm}"]
    return row["admitted"] == "conflict", row["grounded"] and truth == "conflict"


def cases(audit):
    by_family = defaultdict(dict)
    for key, label, _ in study.cases():
        family, witness, _ = key.split("/")
        by_family[family].setdefault(witness, {})[label] = key

    for family, items in by_family.items():
        for sides in combinations(items, 2):
            for truth in product(("open", "conflict"), repeat=2):
                keys = [items[anchor][target] for anchor, target in zip(sides, truth, strict=True)]
                for swapped in (False, True):
                    order = (1, 0) if swapped else (0, 1)
                    name = "+".join(keys[i] for i in order)
                    for arm in MODES:
                        local = [observations(audit, keys[i], truth[i], arm) for i in order]
                        reads = tuple("contradicts" if selected else "unknown" for selected, _ in local)
                        for flags in product((False, True), repeat=2):
                            seen = frozenset(i for i, present in enumerate(flags) if present)
                            expected = "revise" if any(truth[order[i]] == "conflict" for i in seen) else "withhold"
                            acted = "revise" if any(local[i][0] for i in seen) else "withhold"
                            justifications = [local[i][1] for i in seen if local[i][0]]
                            strict = acted == expected and all(justifications)
                            yield family, (name, arm, seen, reads, expected, acted, strict)


def fit_free(path):
    audit = json.loads(path.read_text())
    rows = list(cases(audit))
    frozen, _ = ceiling.stock()
    systems = (("frozen", "learned", frozen), ("greedy", "greedy", {}))
    report = {}
    with patch.object(record, "MODES", MODES):
        for family in ("somalia", "western-sahara"):
            bank = record.collect(r for source, r in rows if source == family)
            report[family] = {}
            for layout in ("split", "overlap"):
                routed = record.evaluate(bank, systems, layout)
                bounds = {}
                for mode in MODES:
                    subset = {key: value for key, value in bank.items() if key[1] == mode}
                    assert len(subset) == 24
                    bounds[mode] = {}
                    for name, feedback in (("adaptive", True), ("independent", False)):
                        _, _, grid = ceiling.tensor(subset, layout, feedback)
                        bounds[mode][name] = exact.maximize(grid)["exact_net"]
                    assert bounds[mode]["adaptive"] + 1e-9 >= max(
                        routed[name]["summary"][mode]["brief_net"] for name, *_ in systems)
                report[family][layout] = {
                    "systems": {name: item["summary"] for name, item in routed.items()}, "exact_bounds": bounds,
                }
    return {"scope": "Replay on paired claims from the same meeting, with both assignments and all open/conflict combinations. "
                     "The literal arm treats all candidate objections as true. A strict objection requires the correct "
                     "decision and adequate proof for each transmitted conflict. This tests transport of scope judgments "
                     "and uses no downstream brief writer or new policy fitting.",
            "packets_per_family": 24, "report": report,
            "sha256": {p.name: sha256(p.read_bytes()).hexdigest() for p in (Path(__file__), path)}}


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("scope_scores", type=Path)
    print(json.dumps(fit_free(p.parse_args().scope_scores), indent=2))
