"""Review the certified transfer under the frozen v1 final rubric."""
import argparse
import json
import re

import torch

import transfer

HERE, E = transfer.HERE, transfer.E


def records():
    return [json.loads(line) for line in (HERE / "evidence/episodes.jsonl").read_text().splitlines()]


def calls_by_arm(row):
    independent = [r["response"] for r in row["independent"]]
    initial = [r["response"] if r else {"input_tokens": 0, "output_tokens": 0}
               for r in (row["first"], row["second"])]
    return {"independent": independent, **{
        name: [*initial, output["response"]] for name, output in row["writers"].items()
    }}


def deck(rows):
    packets = {}
    for row in rows:
        family, _ = row["id"].split("/")
        case = transfer.cases()[family]
        for calls in calls_by_arm(row).values():
            r = E.final_packet(case, calls)
            packets[r["id"]] = r
    return [packets[k] for k in sorted(packets)]


def report(rows):
    marks = E.read(HERE / "marks.json")
    assert set(marks) == {x["id"] for x in deck(rows)}
    model = E.read(transfer.CLARIFY / "results.json")["training"]["weights"]
    results = {}
    for row in rows:
        family, order = row["id"].split("/")
        case = transfer.cases()[family]
        target = "I" if case["gold"] == ["IMPASSE"] else case["gold"][0]
        role_conditions = case["membership"][::1 if order == "0" else -1]
        exact = row["ledger"]["decision"] == target
        if exact:
            claims = row["public_claims"]
            assert all(transfer.LEDGER.truthful_disclosure(message, transfer.route.environment.allowed(
                case["options"], condition)) for message, condition in zip(claims, role_conditions, strict=True))
        out = {"target": target, "public_certificate": row["ledger"]["decision"], "certificate_exact": exact,
               "truthful_declarations": [x == y for x, y in zip(row["extracted"], role_conditions, strict=True)],
               "arms": {}}
        initial = [m for m in row["public_claims"] if m["role"] == row["roles"][0]]
        features = torch.tensor(transfer.route.features(row["roles"], initial), dtype=torch.float64)
        probabilities = transfer.route.probabilities(features, torch.tensor(model, dtype=torch.float64))
        out["frozen_syria_router_action_replay"] = transfer.route.ACTIONS[int(probabilities.argmax())]
        for name, calls in calls_by_arm(row).items():
            blind = E.final_packet(case, calls)
            scored = E.final_score(case, calls, marks[blind["id"]])
            first = next((line.strip() for line in blind["answer"].splitlines() if line.strip()), "")
            alias = re.fullmatch(r"Decision: (?:PACKAGE-)?([A-D]|IMPASSE|UNRESOLVED)", first)
            out["arms"][name] = {**scored, "review_id": blind["id"],
                                  "alias_correct": bool(alias and alias[1] in case["gold"]
                                                        and scored["words"] <= case["word_cap"]
                                                        and calls[-1]["termination"] == "complete"),
                                  "input_tokens": sum(r["input_tokens"] for r in calls),
                                  "output_tokens": sum(r["output_tokens"] for r in calls)}
        results[row["id"]] = out
    aggregate = {}
    for arm in next(iter(results.values()))["arms"]:
        grades = [case["arms"][arm] for case in results.values()]
        aggregate[arm] = {"mechanical_correct": sum(g["mechanical"]["accepted"] for g in grades),
                          "alias_correct": sum(g["alias_correct"] for g in grades),
                          "released": sum(g["release"] for g in grades),
                          "strict": sum(g["strict"] for g in grades),
                          "raw_70_total": [sum(g["raw_70"][i] for g in grades) for i in range(2)],
                          "released_70_total": sum(g["released_70"] for g in grades),
                          "input_tokens": sum(g["input_tokens"] for g in grades),
                          "output_tokens": sum(g["output_tokens"] for g in grades)}
    return {"conditions": results, "summary": aggregate,
            "truthful_declarations": sum(sum(x["truthful_declarations"]) for x in results.values()),
            "correct_public_certificates": sum(x["certificate_exact"] for x in results.values())}


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("mode", choices=("deck", "score"))
    args = cli.parse_args()
    E.emit(deck(records()) if args.mode == "deck" else report(records()))
