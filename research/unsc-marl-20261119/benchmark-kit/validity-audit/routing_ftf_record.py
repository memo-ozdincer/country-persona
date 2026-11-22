"""Plan on a new UN docket and score a fresh bank of receipt-matched Qwen records."""
import argparse
import json
from pathlib import Path
from unittest.mock import patch

import routing_blind_limit as limit
import source_record_run as runner

import numpy as np

base, route, digest = limit.base, limit.route, limit.digest
TASK_PATH = base.space.ROOT / "crossbench/ftf2020/task.json"
ACCESSION = TASK_PATH.with_name("accession.json")
MODEL_REF = base.space.OUT / "peer-evidence-atomic/launch.json"
GUIDE = (
    "Write a supplement to the fixed record in no more than 75 words, using only the supplied annex summaries. "
    "Attribute each national vote explanation accurately and distinguish a national statement from a Council act. "
    "If you have both Russia and US explanations, compare shared repatriation concerns and how the votes differed. "
    "Preserve the reasons and stated limitations. Do not repeat the public record, add outside facts, or label an "
    "unadopted provision as an obligation. Output just the supplement."
)


def read(path):
    return json.loads(path.read_text())


def task():
    value = read(TASK_PATH)
    assert read(ACCESSION)["task_sha256"] == digest(TASK_PATH)
    assert len(value["public_criteria"]) == 5
    return value


def public_payoff():
    fixture = task()
    fields = {row["id"]: 1 << i for i, row in enumerate(fixture["optional_sources"])}
    assert len(fields) == 3
    values = np.zeros(8, dtype=int)
    for rule in fixture["private_criteria"]:
        required = sum(fields[key] for key in rule["required_fields"])
        values += ((route.STATES & required) == required) * rule["points"]
    assert values.tolist() == [0, 7, 7, 28, 7, 14, 14, 35]
    return values


def selections():
    archive = read(limit.PRIOR_BANK)
    priors = {key: np.asarray(p) for group in ("prior_anchors", "prior_stress") for key, p in archive[group].items()}
    # Same public payout vector as UNIFIL, so reuse its pre-existing public candidates.
    pool = archive["historical"]["unifil"]["pool"]
    trained = read(limit.FIT_BANK)["historical_replay"]["unifil"]["policies"]
    return priors, pool, trained


def locks():
    paths = (TASK_PATH, ACCESSION, limit.PRIOR_BANK, limit.FIT_BANK, Path(__file__), Path(limit.__file__))
    return {p.name: digest(p) for p in paths}


def make_plan():
    priors, pool, trained = selections()
    public = public_payoff()
    table = route.receipt_matrix(public, route.TRAIN_LOSS)
    refs = {name: {"independent": route.evaluate(route.best_silent(p, table), p, public, route.TRAIN_LOSS)["net"]}
            for name, p in priors.items()}
    choice = limit.solve({"pool": pool, "results": refs}, {"policies": trained}, public, priors)
    return {"scope": "Freeze prior-blind allocation before any writer output. Use the announced 35-point "
                     "supplement rubric, prior set and frozen public-profile candidates. As the announced "
                     "receipt payoff vector matches UNIFIL, its pre-existing public candidates are reused.",
            "locks": locks(), "public_payoff": public.tolist(), "team": choice}


def requests():
    fixture = task()
    for mask in range(1, 8):
        blocks = {row["id"]: row["text"] for i, row in enumerate(fixture["optional_sources"]) if mask & (1 << i)}
        yield {
            "id": f"receipt-{mask}", "evidence_ids": list(blocks), "cap": 160,
            "messages": [
                {"role": "system", "content": GUIDE},
                {"role": "user", "content": json.dumps({"fixed_public_record": fixture["public_record"],
                                                       "annexes_delivered": blocks}, ensure_ascii=False)},
            ],
        }


def episode(generate):
    return [{"family": task()["id"], "final": generate(list(requests()))}]


def run(directory, plan_path):
    planned = read(plan_path)
    assert planned["locks"] == locks()
    assert planned["public_payoff"] == public_payoff().tolist()
    preflight = {**locks(), "frozen_plan": digest(plan_path)}
    with patch.object(runner, "episode", episode), patch.object(runner, "locks", lambda: preflight):
        runner.run(Path(read(MODEL_REF)["model"]), directory)


def captured(directory, plan_path):
    meta = read(directory / "launch.json")
    assert meta["sha256"] == {**locks(), "frozen_plan": digest(plan_path)}
    complete = read(directory / "complete.json")
    trace = directory / "transcript.jsonl"
    finals = directory / "final-records.json"
    assert digest(trace) == complete["transcript_sha256"] and digest(finals) == complete["final_records_sha256"]
    ordered = list(map(json.loads, trace.read_text().splitlines()))
    assert len(ordered) == complete["records"] == 7
    for row, request in zip(ordered, requests(), strict=True):
        assert all(row[key] == value for key, value in request.items())
    assert read(finals)[task()["id"]] == {row["id"]: row["output"] for row in ordered}
    return ordered


def scoring_vector(rows, marks):
    rubric = {r["id"]: r for r in task()["private_criteria"]}
    raw, eligible, details = [35], [35], []
    assert set(marks) == {row["id"] for row in rows}
    for row in rows:
        review = marks[row["id"]]
        quote_points = review["met"]
        body = row["output"]
        for key, quote in quote_points.items():
            assert set(rubric[key]["required_fields"]) <= set(row["evidence_ids"])
            assert quote and quote in body
        assert review["guard"] in {"clear", "failed", "uncertain"} and review["reason"]
        for key, quote in review["issues"].items():
            assert key in rubric or key == "guard"
            assert quote and quote in body
        words = len(body.split())
        points = 35 + sum(rubric[key]["points"] for key in quote_points)
        released = row["ended"] and words <= 75 and review["guard"] == "clear"
        raw.append(points)
        eligible.append(points if released else 0)
        details.append({"id": row["id"], "raw": points, "eligible_points": eligible[-1], "words": words,
                        "ended": row["ended"], "guard": review["guard"], "credit": list(quote_points)})
    assert np.all(np.array(raw) <= 35 + public_payoff())
    return raw, eligible, details


def score(directory, plan_path, annotations):
    body = captured(directory, plan_path)
    planned = read(plan_path)["team"]
    priors, pool, trained = selections()
    tables = {**pool, **trained}
    strategies = []
    for label, mass in planned["feasible_mixture"]["mixture"].items():
        if label in planned["added_policies"]:
            row = planned["added_policies"][label]
            policy, swapped = row["policy"], row["swap_desks"]
        else:
            orientation, name = label.split(":", 1)
            policy, swapped = tables[name], orientation == "swapped"
        strategies.append((base.space.as_policy(policy), swapped, mass))
    assert np.isclose(sum(mass for _, _, mass in strategies), 1.)
    review = read(annotations)
    raw, gated, details = scoring_vector(body, review["rows"])
    outcomes = {}
    for tag, points in (("raw", np.array(raw)), ("release", np.array(gated))):
        table = route.receipt_matrix(points, route.TRAIN_LOSS)
        outcomes[tag] = {}
        for name, prior in priors.items():
            silent = route.best_silent(prior, table)
            reference = route.evaluate(silent, prior, points, route.TRAIN_LOSS)["net"]
            net = sum(mass * route.evaluate(policy, prior.T if swap else prior, points, route.TRAIN_LOSS)["net"]
                      for policy, swap, mass in strategies)
            erased = sum(mass * route.evaluate(policy, prior.T if swap else prior, points, route.TRAIN_LOSS,
                                               force_missing=True)["net"] for policy, swap, mass in strategies)
            outcomes[tag][name] = {"team": net, "optimized_independent": reference,
                                   "team_minus_independence": net - reference,
                                   "request_erasure_drop": net - erased}
    return {"scope": review["scope"], "bank_sha256": digest(directory / "transcript.jsonl"),
            "annotations_sha256": digest(annotations), "policy_plan_sha256": digest(plan_path),
            "raw_vector": raw, "eligible_vector": gated, "records": details, "results": outcomes}


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("mode", choices=("plan", "run", "check", "score"))
    cli.add_argument("--directory", type=Path)
    cli.add_argument("--plan", type=Path)
    cli.add_argument("--annotations", type=Path)
    args = cli.parse_args()
    if args.mode == "run":
        run(args.directory, args.plan)
    else:
        if args.mode == "plan":
            result = make_plan()
        elif args.mode == "score":
            result = score(args.directory, args.plan, args.annotations)
        else:
            result = list(requests())
        print(json.dumps(result, indent=2, ensure_ascii=False))
