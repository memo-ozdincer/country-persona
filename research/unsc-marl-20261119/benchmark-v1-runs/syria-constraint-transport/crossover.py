"""Score the two crossed writer inputs with the same frozen chair."""
import argparse
import json
from pathlib import Path
from unittest.mock import patch

import replay

E, HERE = replay.E, replay.HERE
KEY = "syria-impasse/peer/1"
FILES = (Path(__file__), HERE / "writer-crossover-protocol.md", HERE / "evidence/complete.json",
         replay.BASE / "evidence/complete.json", E.HERE / "release.json")


def inputs():
    _, case, order, original, projected, _ = next(row for row in replay.contexts() if row[0] == KEY)
    row = next(r for r in E.read(HERE / "evidence/episodes.json") if r["episode"] == KEY)
    new_reply = dict(original[1], **row["note"]["response"])
    old_prompt = E.build_request(case, "peer", order, original[:2])
    new_prompt = E.build_request(case, "peer", order, [projected, new_reply])
    assert row["final"]["request"] == new_prompt
    for name, notes in (("raw_opening_projected_reply", [original[0], new_reply]),
                        ("projected_opening_raw_reply", [projected, original[1]])):
        request = E.build_request(case, "peer", order, notes)
        assert request != old_prompt and request != new_prompt
        assert request["max_output_tokens"] == old_prompt["max_output_tokens"]
        before, after = (json.loads(r["messages"][1]["content"]) for r in (old_prompt, request))
        old_notes, new_notes = before.pop("notes"), after.pop("notes")
        assert sum(a != b for a, b in zip(old_notes, new_notes, strict=True)) == 1 and before == after
        yield name, case, notes, request


def collect(generate, directory):
    rows = [{"arm": name, "request": request, "response": generate(request)}
            for name, _, _, request in inputs()]
    (directory / "crossed.json").write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
    (directory / "crossover-lock.json").write_text(json.dumps(
        {str(p.relative_to(HERE.parents[1])): replay.digest(p) for p in FILES}, indent=2) + "\n")


def verify(directory):
    from transformers import AutoTokenizer

    assert all(replay.digest(directory / f) == stamp for f, stamp in E.read(directory / "complete.json").items())
    assert E.read(directory / "crossover-lock.json") == {
        str(p.relative_to(HERE.parents[1])): replay.digest(p) for p in FILES}
    tokenizer = AutoTokenizer.from_pretrained(replay.baseline.MODEL, local_files_only=True)
    eos = tokenizer.convert_tokens_to_ids("<|im_end|>")
    raw = map(json.loads, (directory / "tokens.jsonl").read_text().splitlines())
    for row, token, (name, _, _, req) in zip(E.read(directory / "crossed.json"), raw, inputs(), strict=True):
        assert row["arm"] == name and row["request"] == req and token["response"] == row["response"]
        assert token["input_ids"] == replay.baseline.prompt(tokenizer, req)
        ids = token["output_ids"]
        assert len(ids) == row["response"]["output_tokens"] and eos not in ids[:-1]
        assert (ids[-1] == eos) == (row["response"]["termination"] == "complete")
        assert tokenizer.decode(ids, skip_special_tokens=True).strip() == row["response"]["text"]
    return {"verified_crossed_calls": 2, "optimizer_updates": 0}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("run", "verify"))
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    if args.mode == "run":
        with patch.object(replay.baseline.suite, "collect", collect):
            replay.baseline.run(args.directory)
    else:
        E.emit(verify(args.directory))
