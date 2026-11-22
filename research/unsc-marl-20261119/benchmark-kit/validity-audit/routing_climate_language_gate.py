"""Check the new chair language using the frozen scope questions and replay the result."""
import argparse
from copy import deepcopy
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import routing_climate_note_budget_writer as writer
import routing_scope_gate_transfer as specification

channel, runner, digest, read = writer.channel, writer.runner, writer.digest, writer.read
climate = specification.climate
BASE = channel.transfer.base.space.OUT / "climate2021-note-budget-writer"
LABELS = BASE / "annotations.json"


def cases():
    notes, records = writer.capture(BASE)
    records = {row["id"]: row for row in records}
    claims = []
    for name, field, ordinal, gold in (
        ("visible-2", "india-explanation", 0, False),
        ("visible-3", "russia-explanation", 0, True),
        ("visible-3", "india-explanation", 1, True),
    ):
        item = records[name]
        source = notes[f"note-{field}"]["output"]
        assert field in item["evidence_ids"]
        found = [s for s in climate.sentences(item["output"]) if climate.PROPOSAL.search(s) and "sahel" in s.lower()]
        claims.append((f"{name}:{field}", name, found[ordinal], source, gold))
    return claims


def requests():
    affirmative = climate.affirmative
    for key, _, sentence, source, _ in cases():
        for i, question in enumerate(affirmative.QUESTIONS):
            yield affirmative.make_request(f"{key}/support-{i}", sentence, source, question)
        for i, question in enumerate(climate.EXTRACTION_QUESTIONS):
            yield {"id": f"{key}/restriction-{i}", "cap": 4, "messages": [
                {"role": "system", "content": climate.EXTRACTION_SYSTEM},
                {"role": "user", "content": json.dumps({"candidate_sentence": sentence, "question": question}, ensure_ascii=False)},
            ]}


def locks():
    return {**writer.locks(), "judgment_script": digest(Path(__file__)),
            "scope_rule_script": digest(Path(specification.__file__)),
            "trimmed_trace": digest(BASE / "transcript.jsonl"), "trimmed_labels": digest(LABELS)}


def episode(generate):
    return [{"family": "climate-language-gate", "final": generate(list(requests()))}]


def score(directory):
    assert read(directory / "launch.json")["sha256"] == locks()
    complete = read(directory / "complete.json")
    trace, final = directory / "transcript.jsonl", directory / "final-records.json"
    assert digest(trace) == complete["transcript_sha256"] and digest(final) == complete["final_records_sha256"]
    rows = list(map(json.loads, trace.read_text().splitlines()))
    assert len(rows) == complete["records"]
    for r, expected in zip(rows, requests(), strict=True):
        assert all(r[k] == v for k, v in expected.items())
    values = {r["id"]: r["output"] for r in rows}
    assert read(final)["climate-language-gate"] == values

    notes, records = writer.capture(BASE)
    annotations = deepcopy(read(LABELS))
    edited = {row["id"]: dict(row) for row in records}
    judgments = {}
    for key, label, sentence, source, expected in cases():
        raw = {mode: [values[f"{key}/{mode}-{i}"] for i in range(2)] for mode in ("support", "restriction")}
        binary = {mode: [climate.affirmative.factored.normalized(r, 0) for r in pair] for mode, pair in raw.items()}
        release = specification.admissions(**binary)["both"]
        judgments[key] = {"candidate": sentence, "evidence": source, "raw": raw, "released": release,
                          "expected": expected}
        if not release:
            row = edited[label]
            assert row["output"].count(sentence) == 1
            row["output"] = " ".join(row["output"].replace(sentence, "", 1).split())
            mark = annotations["rows"][label]
            mark["met"] = {k: quote for k, quote in mark["met"].items() if quote in row["output"]}
            mark["note_support"] = {k: spans for k, spans in mark["note_support"].items() if k in mark["met"]}
            if mark["issues"].get("guard") and mark["issues"]["guard"] in sentence:
                mark["guard"] = "clear"
                mark["reason"] = "Withholding the disallowed sentence removes the sole rated scope error."
                del mark["issues"]["guard"]
    annotations["scope"] = "The frozen two-check rule audits three actual scope-bearing sentences. "
    annotations["scope"] += "Existing manual release and evidence review covers all other assertions."
    with TemporaryDirectory() as tmp:
        review = Path(tmp) / "annotation.json"
        review.write_text(json.dumps(annotations))
        with patch.object(channel, "capture", return_value=(notes, list(edited.values()))):
            replay = channel.score(BASE, review)
    return {"trace_sha256": digest(trace), "checks": judgments,
            "edited_supplements": {k: v["output"] for k, v in edited.items() if k in ("visible-2", "visible-3")},
            "score": replay["arms"]["visible"], "scope": annotations["scope"]}


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("mode", choices=("check", "run", "score"))
    cli.add_argument("directory", type=Path, nargs="?")
    args = cli.parse_args()
    if args.mode == "run":
        with patch.object(runner, "episode", episode), patch.object(runner, "locks", locks):
            runner.run(Path(read(BASE / "launch.json")["model"]), args.directory)
    else:
        result = score(args.directory) if args.mode == "score" else list(requests())
        print(json.dumps(result, indent=2, ensure_ascii=False))
