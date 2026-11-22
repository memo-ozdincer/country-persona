"""Evaluate the frozen conservative receiver on new model-selected openings."""
import argparse
import json
from pathlib import Path
from unittest.mock import patch

import numpy as np

import warrant_request_safety as safe
import warrant_language_team_selector as select
import warrant_reasons as replay

score = safe.interface
base = score.study
world = safe.world
HERE = world.HERE
EVIDENCE = HERE / "warrant-safety-transfer-evidence"
FAMILY = "warrant-safety-transfer"
SEED = 170824
HISTORY_SEED = 170825
PREVIOUS_DOMAINS = base.domains


def domains():
    generator = np.random.default_rng(SEED)
    seen = set.union(*(base.orbit(x) for x in (*world.domains(), *PREVIOUS_DOMAINS())))
    for _ in range(2):
        options = np.array([generator.choice(64, 4, replace=False) for _ in range(3)])
        cards = np.stack((options // 16, options // 4 % 4, options % 4), axis=-1)
        marker = base.orbit(cards)
        assert not marker & seen
        seen |= marker
        yield cards


def requests():
    with patch.object(base, "domains", domains):
        initial = list(base.requests())
    for row in initial:
        if "/D3/" in row["id"]:
            yield row
        else:
            yield base.phrases.prompt(row["id"], 8, select.SYSTEM, json.loads(row["messages"][-1]["content"]))


def episode(generate):
    notes = list(requests())
    rows = {}
    for cap in (8, 25):
        batch = [row for row in notes if row["cap"] == cap]
        for start in range(0, len(batch), 8):
            rows.update(generate(batch[start:start + 8]))
    return [{"family": FAMILY, "final": rows}]


def pins():
    files = (Path(__file__).resolve(), EVIDENCE / "protocol.md", Path(safe.__file__), Path(select.__file__),
             Path(score.__file__), Path(replay.__file__))
    return {**base.pins(), **{str(p.relative_to(HERE)): base.phrases.runner.digest(p) for p in files}}


def verify(folder):
    with patch.multiple(replay, requests=requests, pins=pins, FAMILY=FAMILY):
        return replay.verify(folder)


def compile_reports(rows, index, cards):
    resolved = {}
    for role, typ in np.ndindex(3, 4):
        key = f"d{index}/D{role+1}/card{typ}"
        row = rows[key]
        if role == 2:
            resolved[key] = row
            continue
        token = row["output"]
        text = ""
        if row["ended"] and token in score.PACKAGES:
            slot = score.PACKAGES.index(token)
            text = base.phrases.wire(role, slot, int(cards[role, typ, slot]))
        resolved[key] = {**row, "output": text}
    return resolved


def run(rows):
    rng = np.random.default_rng(HISTORY_SEED)
    report = []
    for i, cards in enumerate(domains()):
        task = world.Workshop(cards)
        styles = base.fitted(task)
        observed, info = score.reports(compile_reports(rows, i, cards), i, cards, styles["mixed"])
        outcomes = {}
        stable = bool((observed >= 0).all())
        for label, correlated in (("uniform", False), ("correlated", True)):
            p = world.prior(correlated)
            draws = rng.random((safe.HISTORIES, safe.PREFIXES[-1]))
            actual, f = score.actual_values(task, p, observed)
            priors = score.predict(task, p, styles, actual, f, draws)
            planner = safe.Planner(task, p)
            if stable:
                robust = safe.evaluate(planner, f, actual, f, draws, True)
            else:
                robust = {str(n): priors["grade_only"] for n in safe.PREFIXES}
            outcomes[label] = {"benchmark": priors, "conservative": robust}
            planner.decision.cache_clear()
        report.append({"domain": i, "cards": cards.tolist(), "intended_slots": styles["mixed"].tolist(),
                       "observed_slots": observed.tolist(), "valid_for_stable_model": stable,
                       "generated": {k: rows[k]["output"] for k in info}, "admission": info, "priors": outcomes})
    return {"domain_seed": SEED, "history_seed": HISTORY_SEED, "paired_histories": safe.HISTORIES, "domains": report}


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("mode", choices=("run", "verify", "score"))
    cli.add_argument("directory", type=Path)
    cli.add_argument("--model", type=Path)
    args = cli.parse_args()
    if args.mode == "run":
        assert len(list(requests())) == 24
        with patch.multiple(base.phrases.runner, episode=episode, locks=pins):
            base.phrases.runner.run(args.model, args.directory)
    elif args.mode == "verify":
        print(json.dumps({"verified_generations": len(verify(args.directory))}))
    else:
        print(json.dumps(run(verify(args.directory)), indent=2))
