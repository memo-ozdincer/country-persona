"""Collect balanced answer-letter observations from frozen UN scope probes."""
import argparse
import json
from pathlib import Path
import sys
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
RUNS = HERE.parent
FIT = RUNS / "reporting-2739/learned-admission"
MYANMAR = RUNS / "myanmar-frozen-admission"
OUT = HERE / "evidence"
sys.path.insert(0, str(FIT))
import held
import team

e = held.e
CYCLES = ([1, 2, 0], [2, 0, 1])


def old_rows():
    routed = [row for row in map(json.loads, (team.ARCHIVE / "actions.jsonl").read_text().splitlines())
              if row["observation"][0] == "routed"]
    myanmar = list(map(json.loads, (MYANMAR / "evidence/calls.jsonl").read_text().splitlines()))
    return routed + myanmar


def identity():
    rows = [row for row in old_rows() if row["observation"][2] == 0]
    assert len(rows) == 27 and all(row["legal"] == [0, 1, 2] for row in rows)
    return rows


def requests():
    for row in identity():
        group, key, _ = row["observation"]
        system, user = row["messages"]
        payload = json.loads(user["content"])
        labels = list(payload["options"].values())
        assert labels == list(held.archived.OPTIONS)
        for n, order in enumerate(CYCLES, start=2):
            contents = payload | {"options": {letter: labels[i] for letter, i in zip("ABC", order, strict=True)}}
            yield {"observation": [group, key, n], "legal": order, "messages": [
                system, user | {"content": json.dumps(contents, ensure_ascii=False)}], "max_output_tokens": 2}


def plan():
    release = held.report.RELEASE
    files = (Path(__file__), HERE / "protocol.md", Path(held.__file__), Path(held.base.__file__),
             Path(team.__file__), team.ARCHIVE / "actions.jsonl", team.ARCHIVE / "results.json",
             team.ARCHIVE / "complete.json", MYANMAR / "plan.json", MYANMAR / "verified.json",
             MYANMAR / "evidence/calls.jsonl", release / "release.json")
    table = list(requests())
    assert len(table) == 54
    native = team.read(MYANMAR / "verified.json")["evidence_sha256"]
    assert native["calls.jsonl"] == team.pin(MYANMAR / "evidence/calls.jsonl")
    assert team.read(team.ARCHIVE / "complete.json")["sha256"] == team.pin(team.ARCHIVE / "actions.jsonl")
    return {"requests": table, "sha256": {str(p.relative_to(team.STUDY)): team.pin(p) for p in files}}


def lock():
    assert plan() == team.read(HERE / "plan.json")


def run():
    with patch.multiple(held, HERE=HERE, OUT=OUT, lock=lock, asks=requests,
                        CASE={"id": "relation-label-balance"}):
        held.run()


def verify():
    from transformers import AutoTokenizer

    lock()
    files = team.read(OUT / "complete.json")
    assert set(files) == {"calls.jsonl", "tokens.jsonl", "launch.json"}
    assert all(team.pin(OUT / k) == digest for k, digest in files.items())
    receipt = team.read(OUT / "launch.json")
    assert receipt["cases"] == ["relation-label-balance"] and receipt["optimizer_updates"] == 0
    assert receipt["protocol_sha256"] == team.pin(HERE / "protocol.md")
    assert receipt["checkpoint_index_sha256"] == held.report.plan()["checkpoint_index_sha256"]
    assert receipt["collector_sha256"] == team.pin(Path(held.base.__file__))
    assert receipt["release_sha256"] == team.pin(held.report.RELEASE / "release.json")
    tok = AutoTokenizer.from_pretrained(held.base.MODEL, local_files_only=True)
    labels, eos = held.ids(tok), tok.convert_tokens_to_ids("<|im_end|>")
    calls, traces = ([json.loads(line) for line in (OUT / k).read_text().splitlines()]
                     for k in ("calls.jsonl", "tokens.jsonl"))
    for expected, actual, trace in zip(requests(), calls, traces, strict=True):
        assert all(actual[k] == value for k, value in expected.items())
        assert trace["input_ids"] == held.base.prompt(tok, expected)
        assert trace["response"] == actual["reply"]
        assert len(trace["input_ids"]) == actual["reply"]["input_tokens"]
        best = max(range(3), key=actual["scores"].__getitem__)
        assert trace["output_ids"] == [labels[best], eos] and actual["reply"]["text"] == "ABC"[best]
        assert 0 <= actual["legal_mass"] <= 1
    assert len(calls) == 54
    return {"records": len(calls), "evidence_sha256": files,
            "input_tokens": sum(r["reply"]["input_tokens"] for r in calls),
            "output_tokens": sum(r["reply"]["output_tokens"] for r in calls)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("plan", "run", "verify"))
    mode = parser.parse_args().mode
    if mode == "run":
        run()
    else:
        e.emit({"plan": plan, "verify": verify}[mode]())
