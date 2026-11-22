"""Calibrate blinded release judgments on original, scoped and controlled records."""
import argparse
from itertools import batched
import json
from pathlib import Path
from unittest.mock import patch

import writer

HERE = writer.HERE
runner, digest, read, replay = writer.runner, writer.digest, writer.read, writer.replay
BANKS = (HERE / "writer-evidence", HERE / "scoped-evidence")
ORDER = (("clear", "failed", "uncertain"), ("failed", "clear", "uncertain"))
GUIDE = (
    "Check the candidate supplement as a historical Council record. Use only the evidence packet. "
    "Mark FAILED if it clearly adds an unsupported claim or materially mixes up documents, proposals, votes, "
    "reasons, national speakers or legal effects. Mark UNCERTAIN only for consequential ambiguity. "
    "Mark CLEAR if its claims are supported. Missing details and repeated content alone do not affect this judgment. "
    "For a proposed amendment, distinguish failure to reach the vote threshold from a permanent member veto of the draft. "
    "Keep proposal language and national statements attributed. A claimed sole rationale or absence of other vote "
    "explanations needs explicit support. Reply with exactly one code from the supplied codebook."
)
ANCHORS = {
    "amendment_775/slip": (
        "S/2023/775 received six votes in favour, one against and eight abstentions. It fell short of the vote threshold.",
        "S/2023/775 received six votes in favour, one against and eight abstentions. It was defeated by a U.S. veto.",
    ),
    "veto_explanation/matched": (
        "Speaking for the United States, Linda Thomas-Greenfield cited Article 51 and objected that the draft omitted Israel’s right of self-defence.",
        "Speaking for the Council, Linda Thomas-Greenfield issued an Article 51 finding that the draft omitted Israel’s right of self-defence.",
    ),
}


def candidates():
    task = writer.routing.load()
    evidence = {row["id"]: {key: value for key, value in json.loads(row["messages"][1]["content"]).items()
                            if key != "coverage"} for row in writer.requests()}
    result = []
    for bank in BANKS:
        finals = read(bank / "final-records.json")[task["id"]]
        manual = read(bank / "annotations.json")["rows"]
        for key, text in finals.items():
            result.append((f"{bank.name}/{key}", evidence[key], text, manual[key]["guard"]))
    for key, pair in ANCHORS.items():
        for label, text in zip(("clear", "failed"), pair, strict=True):
            result.append((f"anchor/{key}/{label}", evidence[key], text, label))
    return result


def request_labels():
    tasks = []
    for number, (name, evidence, text, expected) in enumerate(candidates()):
        for i, order in enumerate(ORDER):
            alphabet = dict(zip("ABC", order, strict=True))
            prompt = {"evidence": evidence, "candidate": text, "codebook": alphabet}
            row = replay.request(f"record-{number:02}-{i}", 4, GUIDE, prompt, [])
            tasks.append((row, name, alphabet, expected))
    return tasks


def episode(generate):
    results = {}
    for batch in batched([row for row, *_ in request_labels()], 8):
        results.update(generate(list(batch)))
    return [{"family": writer.routing.load()["id"], "final": results}]


def locks():
    result = {**writer.locks(), "guard_judge": digest(Path(__file__))}
    for bank in BANKS:
        for name in ("final-records.json", "annotations.json"):
            result[f"{bank.name}/{name}"] = digest(bank / name)
    return result


def run(directory):
    with patch.object(runner, "episode", episode), patch.object(runner, "locks", locks):
        runner.run(Path(read(writer.MODEL)["model"]), directory)


def report(directory):
    with patch.object(replay, "episode", episode), patch.object(replay, "locks", locks):
        outputs = replay.verify(directory)
    labeled = {}
    for row, key, alphabet, target in request_labels():
        actual = outputs[row["id"]]
        verdict = alphabet.get(actual["output"].strip()) if actual["ended"] else None
        entry = labeled.setdefault(key, {"expected": target, "predicted": []})
        entry["predicted"].append(verdict)
    stats = {}
    for label, accepted in (("writer", lambda name: not name.startswith("anchor/")),
                            ("anchors", lambda name: name.startswith("anchor/"))):
        rows = [row for name, row in labeled.items() if accepted(name)]
        stats[label] = {"cases": len(rows),
                        "valid_calls": sum(output is not None for row in rows for output in row["predicted"]),
                        "cases_stable_and_correct": sum(row["predicted"] == [row["expected"]] * 2 for row in rows),
                        "cases_order_sensitive": sum(a != b for a, b in (row["predicted"] for row in rows)),
                        "guard_failures_missed_by_at_least_one_order": sum(row["expected"] == "failed"
                                                                          and row["predicted"] != ["failed"] * 2
                                                                          for row in rows),
                        "clear_cases_failed_by_at_least_one_order": sum(row["expected"] == "clear"
                                                                       and "failed" in row["predicted"] for row in rows)}
    return {"scope": "Frozen Qwen3.5-4B judges guards blind to method and reference verdict. The same model wrote both "
                     "banks. Reference verdicts are same-assistant annotations, and anchors are authored.",
            "trace_sha256": digest(directory / "transcript.jsonl"), "stats": stats, "records": labeled}


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("mode", choices=("run", "score"))
    cli.add_argument("directory", type=Path)
    args = cli.parse_args()
    if args.mode == "run":
        run(args.directory)
    else:
        print(json.dumps(report(args.directory), indent=2))
