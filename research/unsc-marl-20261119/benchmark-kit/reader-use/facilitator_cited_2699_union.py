"""Merge independently verified witnesses while rejecting stable false citations."""
import argparse
import json
from pathlib import Path
from unittest.mock import patch

import numpy as np

import facilitator_cited_2699_score as previous

study = previous.study
source = previous.source
archive = previous.archive


def run(report):
    checks = report["checks"]
    decks = study.decks()
    recovered, stable_errors, rejected = {}, {}, []
    for name, deck in decks.items():
        variants = {group: [checks[f"{name}/{group}/{i}"]["fields"] for i in range(2)]
                    for group in ("full", "withheld")}
        proofs = []
        for slot, alternatives in enumerate(zip(*variants["full"], strict=True)):
            authorized = deck["statements"][deck["witnesses"][slot]]
            matches = [i for i, field in enumerate(alternatives)
                       if field["correct"] and field["exact_source"] == authorized]
            if matches:
                proofs.append({"slot": slot, "reads": matches, "source": authorized})
        recovered[name] = proofs
        n = deck["foil_slot"]
        alternatives = [read[n] for read in variants["withheld"]]
        if all(f["unexpected_evidence"] for f in alternatives):
            a, b = (f["exact_source"] for f in alternatives)
            if a == b:
                stable_errors[name] = a
        for group, n_reads in (("withheld", 2), ("foil", 1)):
            for i in range(n_reads):
                field = checks[f"{name}/{group}/{i}"]["fields"][n]
                assert field["expected"] == "X"
                if field["unexpected_evidence"]:
                    rejected.append({"case": f"{name}/{group}/{i}", "source": field["exact_source"]})
    mask = np.zeros(4, dtype=bool)
    for name, entries in recovered.items():
        if len(entries) == len(decks[name]["witnesses"]):
            mask[decks[name]["topic"]] = True
    old = json.loads((archive.EVIDENCE / "results.json").read_text())
    cases = {}
    with patch.object(source, "packet", archive.packet):
        for label in source.PRIORS:
            prior = source.ROUTE.TEST_PRIORS[label]
            policies = source.policies(prior)
            cases[label] = {name: source.distribution(policy, prior, old["decoded"], np.broadcast_to(mask, (4, 4)))
                            for name, policy in policies.items()}
            if mask[1:].all():
                typed = old["priors"][label]["all_arms"]
                assert all(abs(case["net"] - typed[name]["typed"]["net"]) < 1e-12
                           for name, case in cases[label].items())
    return {"scenario": "Post hoc registry-verified merge. Same two generations per available deck.",
            "admitted_topics": np.flatnonzero(mask).tolist(), "recovered": recovered,
            "stable_false_citations_across_orders": stable_errors, "rejected_control_citations": rejected,
            "priors": cases}


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("report", type=Path)
    print(json.dumps(run(json.loads(cli.parse_args().report.read_text())), indent=2, ensure_ascii=False))
