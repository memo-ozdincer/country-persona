"""Render a bounded workshop record directly from the admitted evidence."""
import argparse
from itertools import product
import json
from pathlib import Path
import re

import warrant_live as study
import warrant_live_authorized as authorized
from check import warrant, winners


def parse_reports(evidence):
    facts = []
    for line in evidence.values():
        m = re.fullmatch(r"D([12]) reports grade ([0-3]) for ([ABC])\.", line)
        if m is None:
            raise ValueError("An admitted report does not match the grade format")
        role, grade, package = m.groups()
        facts.append((int(role) - 1, study.fit.PACKAGES.index(package), int(grade)))
    return facts


def ranking(pair):
    entries = []
    for package, grades in zip(study.fit.PACKAGES, zip(*pair, strict=True), strict=True):
        weaker = min(grades)
        entries.append(f"{package} lower grade {weaker}, total {sum(grades)}" if weaker else f"{package} excluded")
    return "The one compatible card pair implies " + ", ".join(entries) + "."


def compile_record(roles, evidence):
    facts = parse_reports(evidence)
    compatible = [world for world in product(*roles)
                  if all(world[side][package] == grade for side, package, grade in facts)]
    expected = [winners(study.fit.MENU, world, "full") for world in compatible]
    outcome = warrant(expected)
    decision = sorted(outcome)[0].upper()
    if decision == "IMPASSE":
        conclusion = "Every package has a zero grade from at least one delegate in every compatible card pair. The workshop records an impasse."
    elif decision == "UNRESOLVED":
        conclusion = "Compatible card pairs allow different outcomes with no shared permissible decision. The workshop leaves the decision unresolved."
    elif len(compatible) == 1:
        conclusion = f"{ranking(compatible[0])} The workshop recommends {decision} under the lower-grade-first rule."
    else:
        conclusion = f"{decision} ranks first or ties for first under the lower-grade-first rule in every compatible card pair. The workshop recommends {decision}."
    ledgers = " ".join(f"{name}: {text}" for name, text in evidence.items()) or "No grade reports were delivered."
    memo = f"Fictional workshop record. {ledgers} {conclusion}"
    assert len(memo.split()) <= 90
    return {"decision": decision, "evidence": list(evidence), "memo": memo}


def run(rows):
    result = {}
    for key, roles, evidence, proof, mode in study.views(rows):
        if mode != "direct":
            continue
        record = compile_record(roles, evidence)
        assert record["decision"] in proof["permitted_decisions"]
        assert all(f"{name}: {text}" in record["memo"] for name, text in evidence.items())
        result[key.rsplit("/", 1)[0]] = record
    return result


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("directory", type=Path)
    args = cli.parse_args()
    print(json.dumps(run(authorized.verify(args.directory)), ensure_ascii=False, indent=2))
