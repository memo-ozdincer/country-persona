"""Compare reviewed records under both writer prompts and replay archived source delivery."""
import argparse
from itertools import product
import json
from pathlib import Path
import re

import facilitator_authority_writer as run
import facilitator_requested_evidence_score as prior

ARMS = ("peer", "independent", "verbatim_query", "direct_one")


def records(directory):
    rows = run.verify(directory)
    out = {}
    for name, sid, payload in run.cases():
        unit = run.previous.packet()["tasks"][name]
        out[f"{name}/{sid}"] = {
            "question": payload["editorial_question"],
            "criterion": unit["criterion"],
            "sources": payload["documentary_evidence"],
            "output": rows[f"{name}/{sid}/final"]["output"],
        }
    return rows, out


def metrics(row, grade, evidence, target):
    score = prior.grade(grade, row["output"], evidence, target)
    verdict = score.pop("strict_fields")
    return {
        **score, "editorial": grade["editorial"][0] == "met",
        "integrity": grade["integrity"][0] == "met",
        "authority": grade["limit"][0] == "met",
        "literal_urges": bool(re.search(r"\burges\s+(?:States\s+to\s+)?(?:investigations|conduct\b)",
                                         row["output"], re.I)),
        "strict": verdict and row["ended"] and len(row["output"].split()) <= 95,
        "ended": row["ended"],
        "input_tokens": len(row["input_ids"]), "output_tokens": len(row["output_ids"]),
    }


def summary(rows):
    return {
        "views": len(rows),
        **{k: sum(row[k] for row in rows)
           for k in ("editorial", "authority", "integrity", "literal_urges", "strict", "ended")},
        "mean_points": sum(row["points"] for row in rows) / len(rows),
        "writer_input_tokens": sum(row["input_tokens"] for row in rows),
        "writer_output_tokens": sum(row["output_tokens"] for row in rows),
    }


def receipt_ceilings(by_view, tasks):
    decks = tuple(dict.fromkeys(task["deck"] for task in tasks.values()))
    report = {}
    for writer in ("original", "revised"):
        output = {}
        for measure in ("points", "strict"):
            def value(name, sid):
                return by_view[f"{name}/{sid}"][writer][measure]

            def mean(choices):
                return sum(value(name, sid) for name, sid in choices.items()) / len(tasks)

            blind = []
            for cards in product(("A", "B"), repeat=len(decks)):
                policy = dict(zip(decks, cards, strict=True))
                blind.append(mean({name: policy[task["deck"]] for name, task in tasks.items()}))
            targeted = {name: task["target"] for name, task in tasks.items()}
            output[measure] = {
                "best_blind": max(blind),
                "send_relevant": mean(targeted),
                "best_task_aware": sum(max(value(name, "A"), value(name, "B"))
                                      for name in tasks) / len(tasks),
                "wrong_card_ties": [name for name, sid in targeted.items()
                                    if value(name, "A") == value(name, "B")],
                "wrong_card_wins": [name for name, sid in targeted.items()
                                    if value(name, sid) < value(name, "B" if sid == "A" else "A")],
            }
        report[writer] = output
    return report


def score(rows, items, grades):
    assert grades.keys() == items.keys()
    previous = run.previous.verify(run.SOURCE)
    review = json.loads((run.SOURCE / "grades.json").read_text())
    old_items = prior.review_items(previous)
    keys = {address: key for key, item in old_items.items() for address in item["addresses"]}
    exact = {}
    for name, task in run.previous.packet()["tasks"].items():
        for arm in ARMS:
            address = f"{name}/{arm}/final"
            sid, = run.previous.receipt(name, arm, previous)
            payload = json.loads(previous[address]["messages"][-1]["content"])
            assert payload == {
                "editorial_question": items[f"{name}/{sid}"]["question"],
                "documentary_evidence": items[f"{name}/{sid}"]["sources"],
            }
            exact.setdefault(f"{name}/{sid}", []).append(address)
    assert exact.keys() == items.keys()
    by_view = {}
    for key, item in items.items():
        target = run.previous.packet()["tasks"][key.split("/")[0]]["target"]
        old, *_ = exact[key]
        outputs = {previous[address]["output"] for address in exact[key]}
        by_view[key] = {
            "original_address": old,
            "relevant_card_delivered": key.endswith(f"/{target}"),
            "original": metrics(previous[old], review[keys[old]], item["sources"], target),
            "revised": metrics(rows[f"{key}/final"], grades[key], item["sources"], target),
        }
        if len(outputs) > 1:
            by_view[key]["original_output_sensitivity"] = {
                address: metrics(previous[address], review[keys[address]], item["sources"], target)
                for address in exact[key]
            }
    replay = {}
    for arm in ARMS:
        views = [f"{name}/{run.previous.receipt(name, arm, previous)[0]}"
                 for name, *_ in run.previous.cases()]
        replay[arm] = {
            "selected_views": views,
            "original": summary([by_view[key]["original"] for key in views]),
            "revised": summary([by_view[key]["revised"] for key in views]),
        }
    return {
        "scope": "One exposed meeting. Exact original documentary input retained under the new prompt. "
                 "Original comparator is the first archived output for each matching view, preordered by policy. "
                 "Archived selections replayed with one reviewed new final per view. Same-assistant review.",
        "views": by_view,
        "cohorts": {tag: {arm: summary([row[arm] for row in by_view.values()
                                         if row["relevant_card_delivered"] == relevant])
                           for arm in ("original", "revised")}
                    for tag, relevant in (("relevant", True), ("irrelevant", False))},
        "archived_route_replay": replay,
        "one_card_reward_ceilings": receipt_ceilings(by_view, run.previous.packet()["tasks"]),
    }


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("directory", type=Path)
    p.add_argument("--grades", type=Path)
    args = p.parse_args()
    rows, items = records(args.directory)
    print(json.dumps(score(rows, items, json.loads(args.grades.read_text())) if args.grades else items,
                     indent=2, ensure_ascii=False))
