"""Paired receipt-specific writer transfer on the 2021 climate-security vote."""
import argparse
import json
from pathlib import Path
from unittest.mock import patch

import numpy as np

import routing_ftf_bounded_writer as bounded
import routing_ftf_script_control as scripts
import routing_ftf_writer_effects as effects

original, runner, digest, read = bounded.original, bounded.runner, bounded.digest, bounded.read
route, base = effects.route, effects.base
TASK = base.space.ROOT / "crossbench/climate2021/task.json"
ACCESSION = TASK.with_name("accession.json")
MODEL_REF = base.space.OUT / "ftf2020-visible-writer/launch.json"
ARMS = ("all", "visible")
CAP = 160
OPEN = "Write a plain-language supplement of at most 75 words. Use one sentence per delivered annex, in its given order."
CLOSE = (
    "Keep each explanation attributable to its owner. Use the public record only for procedural context. "
    "Avoid restating the public record, attaching legal status to the failed draft, or describing whether evidence "
    "was supplied. Output only the requested sentences."
)


def task():
    fixture = read(TASK)
    assert read(ACCESSION)["task_sha256"] == digest(TASK)
    return fixture


def payoff(fixture):
    fields = {row["id"]: 1 << i for i, row in enumerate(fixture["optional_sources"])}
    values = np.zeros(8, int)
    for row in fixture["private_criteria"]:
        required = sum(fields[key] for key in row["required_fields"])
        values += ((route.STATES & required) == required) * row["points"]
    np.testing.assert_array_equal(values, original.public_payoff())
    return values


def requests():
    fixture = task()
    selected = set(fixture["comparison_fields"])
    for arm in ARMS:
        for mask in range(1, 8):
            delivered = {row["id"]: row["text"] for i, row in enumerate(fixture["optional_sources"]) if mask & (1 << i)}
            tail = "Cover only the delivered annexes."
            guide = [OPEN, *(row["instruction"] for row in fixture["optional_sources"]
                             if arm == "all" or row["id"] in delivered)]
            if arm == "all" or selected <= delivered.keys():
                guide.extend((fixture["comparison_instruction"], "If either annex is absent, make no statement about that delegation's rationale or a shared concern."))
            else:
                guide.append(tail)
            guide.append(CLOSE)
            yield {"id": f"{arm}-{mask}", "cap": CAP, "evidence_ids": list(delivered), "messages": [
                {"role": "system", "content": " ".join(guide)},
                {"role": "user", "content": json.dumps({"fixed_public_record": fixture["public_record"],
                                                       "annexes_delivered": delivered}, ensure_ascii=False)},
            ]}


def per_case_plans():
    public = payoff(task())
    _, learned, independent = effects.frozen_policies()
    candidates, weights, _ = scripts.select()
    scripted = [(p, swap, w) for (p, swap), w in zip(candidates.values(), weights, strict=True)]
    return {"scope": "Before writer outputs. The announced public payoff is identical to the earlier written-ballot case. "
                     "Transfer its learned and independent mixtures and apply the same scripted selection.",
            "payoff": public.tolist(),
            "plans": {name: [[[row.tolist() for row in policy], bool(swap), float(weight)]
                             for policy, swap, weight in group]
                      for name, group in (("learned", learned), ("independent", independent), ("scripted", scripted))}}


def locks(plan_file):
    return {**original.locks(), "climate_task": digest(TASK), "climate_accession": digest(ACCESSION),
            "plan": digest(plan_file), "script": digest(Path(__file__)), "runner": digest(Path(runner.__file__)),
            "writer_reference": digest(MODEL_REF)}


def run(directory, plan_file):
    assert per_case_plans() == read(plan_file)
    plans = list(requests())
    first, alternate = plans[:7], plans[7:]
    for a, b in zip(first, alternate, strict=True):
        assert a["messages"][1:] == b["messages"][1:] and a["cap"] == b["cap"]
    assert first[-1]["messages"] == alternate[-1]["messages"]

    def episode(generate):
        return [{"family": task()["id"], "final": {**generate(first), **generate(alternate[:-1])}}]

    with patch.object(runner, "episode", episode), patch.object(runner, "locks", lambda: locks(plan_file)):
        runner.run(Path(read(MODEL_REF)["model"]), directory)


def captured(directory, plan_file):
    assert read(directory / "launch.json")["sha256"] == locks(plan_file)
    complete = read(directory / "complete.json")
    trace, finals = directory / "transcript.jsonl", directory / "final-records.json"
    assert digest(trace) == complete["transcript_sha256"] and digest(finals) == complete["final_records_sha256"]
    rows = list(map(json.loads, trace.read_text().splitlines()))
    assert len(rows) == complete["records"] == 13
    for observed, planned in zip(rows, list(requests())[:-1], strict=True):
        assert all(observed[k] == v for k, v in planned.items())
    assert read(finals)[task()["id"]] == {r["id"]: r["output"] for r in rows}
    return [*rows, {**rows[6], "id": "visible-7"}]


def score(directory, plan_file, labels):
    rows = captured(directory, plan_file)
    fixture = task()
    notes = read(labels)
    priors, _, _ = original.selections()
    plan = read(plan_file)
    plans = {name: [(base.space.as_policy(p), swap, w) for p, swap, w in group]
             for name, group in plan["plans"].items()}
    outcomes = {}
    for arm in ARMS:
        chair = [r for r in rows if r["id"].startswith(f"{arm}-")]
        marks = {r["id"]: notes["rows"][r["id"]] for r in chair}
        with patch.object(original, "task", return_value=fixture), patch.object(original, "public_payoff", return_value=payoff(fixture)):
            raw, release, detail = original.scoring_vector(chair, marks)
        results = {}
        for vector, credit in (("raw", raw), ("release", release)):
            credit = np.asarray(credit, dtype=int)
            matrix = route.receipt_matrix(credit, route.TRAIN_LOSS)
            results[vector] = {}
            for name, p in priors.items():
                nets = {method: sum(w * route.evaluate(policy, p.T if swap else p, credit, route.TRAIN_LOSS)["net"]
                                    for policy, swap, w in mixture) for method, mixture in plans.items()}
                exact = route.best_silent(p, matrix)
                nets["informed_independence"] = route.evaluate(exact, p, credit, route.TRAIN_LOSS)["net"]
                nets["erase_questions"] = sum(w * route.evaluate(policy, p.T if swap else p, credit, route.TRAIN_LOSS,
                                                                 force_missing=True)["net"]
                                               for policy, swap, w in plans["learned"])
                results[vector][name] = {
                    "nets": nets, "learned_gains": {key: nets["learned"] - v for key, v in nets.items() if key != "learned"},
                }
        outcomes[arm] = {"raw": raw, "release": release, "records": detail, "results": results}
    return {"scope": notes["scope"], "plan_sha256": digest(plan_file), "annotations_sha256": digest(labels),
            "trace_sha256": digest(directory / "transcript.jsonl"), "arms": outcomes}


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("mode", choices=("check", "plan", "run", "score"))
    cli.add_argument("--directory", type=Path)
    cli.add_argument("--plan", type=Path)
    cli.add_argument("--annotations", type=Path)
    args = cli.parse_args()
    if args.mode == "run":
        run(args.directory, args.plan)
    else:
        if args.mode == "plan":
            result = per_case_plans()
        elif args.mode == "score":
            result = score(args.directory, args.plan, args.annotations)
        else:
            result = list(requests())
        print(json.dumps(result, indent=2, ensure_ascii=False))
