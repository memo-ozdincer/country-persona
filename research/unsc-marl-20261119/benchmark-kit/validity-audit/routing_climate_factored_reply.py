"""Separate policy-table selection from the reply writer's source context."""
import argparse
import json
from pathlib import Path
from unittest.mock import patch

import routing_climate_live_fallback as mixed

live, runner, read, digest = mixed.live, mixed.runner, mixed.read, mixed.digest
BASE = live.transfer.base.space.OUT / "climate2021-live-fallback"
SELECT = (
    "Use the incoming question to identify whose vote explanation is requested. If the question is empty, use "
    "the no question row. Look up that row in the reply table, even if it points to a different delegation. "
    "Return only the selected annex ID. Do not write an explanation."
)
WRITE = (
    "Send a brief note based only on the annex below. Attribute the reasons and institutional preferences to "
    "the named delegation and preserve geographic and policy scope. Use complete sentences and at most 55 words. "
    "Do not discuss other annexes or how the source was selected."
)


def selections(previous):
    for name, row in previous.items():
        if name == "question-russia":
            continue
        payload = json.loads(row["messages"][1]["content"])
        payload["local_inventory"] = [{key: value for key, value in item.items() if key != "text"}
                                      for item in payload["local_inventory"]]
        yield live.request(name, 16, SELECT, payload, row["evidence_ids"])


def selected(reply):
    value = reply["output"]
    return value if reply["ended"] and value in reply["evidence_ids"] else ""


def writers(replies):
    needed = {selected(row) for row in replies.values()}
    return [live.request(f"note/{source['id']}", 80, WRITE,
                         {"delegation": source["role"], "annex": source["text"]}, [source["id"]])
            for source in live.sources(7) if source["id"] in needed]


def episode(previous):
    def play(generate):
        choice = generate(list(selections(previous)))
        drafts = writers(choice)
        written = generate(drafts) if drafts else {}
        return [{"family": live.transfer.task()["id"], "final": {**choice, **written}}]
    return play


def locks():
    return {**mixed.locks(), "factored_script": digest(Path(__file__)),
            "mixed_trace": digest(BASE / "transcript.jsonl")}


def run(directory):
    previous = mixed.verify(BASE)
    with patch.object(runner, "episode", episode(previous)), patch.object(runner, "locks", locks):
        runner.run(Path(read(BASE / "launch.json")["model"]), directory)


def summary(directory):
    previous = mixed.verify(BASE)
    expected = locks()
    with patch.object(live, "episode", episode(previous)), patch.object(live, "locks", lambda: expected):
        rows = live.verify(directory)
    cases = read(BASE / "live-summary.json")["results"]
    results = {}
    for key, baseline in cases.items():
        field = selected(rows[key])
        note = rows[f"note/{field}"] if field else None
        admitted = live.admit_note(note, field) if note else None
        results[key] = {"expected_field": baseline["expected_field"], "selected": field,
                        "admitted_field": admitted[0] if admitted else "",
                        "body": admitted[1] if admitted else "",
                        "generated_tokens": len(rows[key]["output_ids"]) + (len(note["output_ids"]) if note else 0),
                        "token_ceiling": 96}
    return {"scope": "Identical questions, reply tables and token ceiling. Selector sees only inventory names and IDs. "
                     "One note per selected annex is reused as a deterministic reply draft within this run.",
            "trace_sha256": digest(directory / "transcript.jsonl"), "results": results}


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("mode", choices=("run", "verify"))
    cli.add_argument("directory", type=Path)
    args = cli.parse_args()
    if args.mode == "run":
        run(args.directory)
    else:
        print(json.dumps(summary(args.directory), indent=2, ensure_ascii=False))
