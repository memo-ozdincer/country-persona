"""Test a learned unavailable-request fallback against a format-matched default."""
import argparse
import json
from pathlib import Path
from unittest.mock import patch

import routing_climate_live_exchange as live

runner, read, digest = live.runner, live.read, live.digest
BASE = live.transfer.base.space.OUT / "climate2021-live-exchange"
WORLDS = {"missing-india": (1, 5), "missing-russia": (2, 6), "held-india": (1, 3)}
CONDITIONS = ("learned", "default", "erased")
GUIDE = (
    "You are a records desk. Read the incoming question and determine which delegation's explanation it asks about. "
    "If the question is empty, use the no question row. Select the annex ID in the reply table for that row, even if "
    "it differs from the delegation asked about. Output the selected annex ID on its own first line, then a note "
    "based only on that annex in at most 55 words. Give its delegation's institutional rationale and preferred scope."
)


def plan():
    frozen = read(live.channel.PLAN)
    assert frozen == live.transfer.per_case_plans()
    (ask, send, reply), swap, weight = max(frozen["plans"]["learned"], key=lambda record: record[2])
    fields = live.sources(7)
    keys = ["no question", *(source["role"] for source in fields)]
    ids = ["", *(source["id"] for source in fields)]
    rows = {}
    for world, (left, right) in WORLDS.items():
        target = ask[left]
        default = next(i for i in range(1, 4) if right & (1 << (i - 1)))
        naive = [default] + [i if right & (1 << (i - 1)) else default for i in range(1, 4)]
        tables = {"learned": dict(zip(keys, [ids[a] for a in reply[right]], strict=True)),
                  "default": dict(zip(keys, [ids[a] for a in naive], strict=True))}
        assert all(all(value in [source["id"] for source in live.sources(right)] for value in table.values())
                   for table in tables.values())
        rows[world] = {"requester_inventory": left, "responder_inventory": right, "question_target": keys[target],
                       "requester_sends": ids[send[left]], "reply_tables": tables}
    for world in ("missing-india", "missing-russia"):
        row = rows[world]
        assert row["reply_tables"]["learned"][row["question_target"]] == "china-explanation"
        assert row["reply_tables"]["default"][row["question_target"]] == row["requester_sends"]
    assert rows["held-india"]["reply_tables"]["learned"] == rows["held-india"]["reply_tables"]["default"]
    return {"component_weight": weight, "swapped": swap, "worlds": rows}


def russian_question():
    _, draft = live.opening()
    return {**draft, "id": "question-russia", "messages": [
        draft["messages"][0], {"role": "user", "content": json.dumps({"delegation_to_ask_about": "Russian Federation"})},
    ]}


def replies(india, russia):
    queries = {"India": live.admit_question(india), "Russian Federation": live.admit_question(russia)}
    for world, setup in plan()["worlds"].items():
        inventory = live.sources(setup["responder_inventory"])
        for condition in CONDITIONS if world.startswith("missing-") else ("learned",):
            table = setup["reply_tables"]["learned" if condition == "erased" else condition]
            payload = {"incoming_question": "" if condition == "erased" else queries[setup["question_target"]],
                       "local_inventory": [{key: row[key] for key in ("id", "role", "text")} for row in inventory],
                       "reply_table": table}
            yield live.request(f"{world}/{condition}", 96, GUIDE, payload, [source["id"] for source in inventory])


def episode(previous):
    def play(generate):
        question = generate([russian_question()])
        answers = generate(list(replies(previous["question"], question["question-russia"])))
        return [{"family": live.transfer.task()["id"], "final": {**question, **answers}}]
    return play


def locks():
    return {**live.locks(), "fallback_script": digest(Path(__file__)),
            "reused_question_trace": digest(BASE / "transcript.jsonl")}


def run(directory):
    previous = live.verify(BASE)
    with patch.object(runner, "episode", episode(previous)), patch.object(runner, "locks", locks):
        runner.run(Path(read(BASE / "launch.json")["model"]), directory)


def verify(directory):
    previous = live.verify(BASE)
    expected = locks()
    with patch.object(live, "episode", episode(previous)), patch.object(live, "locks", lambda: expected):
        return live.verify(directory)


def summary(directory):
    rows = verify(directory)
    results = {}
    possibilities = plan()["worlds"]
    for key, row in rows.items():
        if key == "question-russia":
            continue
        world, condition = key.split("/")
        spec = possibilities[world]
        table = spec["reply_tables"]["default" if condition == "default" else "learned"]
        target = table["no question" if condition == "erased" else spec["question_target"]]
        admitted = live.admit_note(row)
        field, body = admitted if admitted is not None else ("", "")
        results[key] = {"expected_field": target, "admitted_field": field,
                        "matches_table": field == target, "admitted_text": body,
                        "adds_distinct_annex": bool(field and field != spec["requester_sends"]),
                        "generated_tokens": len(row["output_ids"])}
    return {"trace_sha256": digest(directory / "transcript.jsonl"),
            "questions": {"India": rows.get("question-india", {}).get("output", "See archived live trace"),
                          "Russia": rows["question-russia"]["output"]},
            "results": results}


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("mode", choices=("plan", "run", "verify"))
    cli.add_argument("directory", type=Path, nargs="?")
    args = cli.parse_args()
    if args.mode == "run":
        run(args.directory)
    else:
        print(json.dumps(plan() if args.mode == "plan" else summary(args.directory), ensure_ascii=False, indent=2))
