"""Collect each one-question branch of the locked archived evidence episodes."""
import argparse
import json
from pathlib import Path
import sys
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
PUBLIC = HERE.parent / "syria-public-evidence"
sys.path.insert(0, str(PUBLIC))
import reader

E, BASE = reader.E, reader.baseline
FIELDS = reader.FIELDS


def requests():
    rows = []
    for key, case, notes in reader.pair_inputs():
        for turn, (speaker, _) in enumerate(notes):
            slot = case["roles"].index(speaker)
            own = case["owned"][slot]
            assert len(own) == 1 and case["owned"][1-slot][0]["id"] != own[0]["id"]
            system = (
                "You are the named replying workshop delegate. The chair is asking you to state your own full "
                "fictional requirement. State the complete requirement from your private card exactly in semantic "
                "terms. Ignore guesses in the notes and do not supply any other person's mandate. Your answer "
                "declares that you could accept exactly the menu options satisfying this one requirement. "
                "Output one JSON object with exactly two string keys, field and value. No prose."
            )
            payload = {"speaker": speaker, "question": "What is your own complete fictional workshop requirement?",
                       "own_card": own[0]["text"], "menu": [row["id"] + ": " + row["text"] for row in case["options"]],
                       "permitted_requirements": FIELDS, "prior_public_notes": [
                           {"speaker": name, "text": text} for name, text in notes]}
            rows.append({"id": f"{key}/ask-{turn}", "max_output_tokens": 100, "messages": [
                {"role": "system", "content": system}, {"role": "user", "content": json.dumps(payload, ensure_ascii=False)}
            ]})
    return rows


def pins():
    files = (Path(__file__), HERE / "protocol.md", HERE / "requests.json", PUBLIC / "recovery.json",
             PUBLIC / "evidence/complete.json", E.HERE / "release.json")
    return {str(p.relative_to(HERE.parent.parent)): BASE.sha(p) for p in files}


def collect(generate, directory):
    frozen = E.read(HERE / "requests.json")
    assert frozen == requests()
    for request in frozen:
        BASE.suite.append(directory / "responses.jsonl", {"id": request["id"], "response": generate(request)})
    (directory / "clarification-lock.json").write_text(json.dumps(pins(), indent=2) + "\n")


def verify(directory):
    from transformers import AutoTokenizer

    manifest = E.read(directory / "complete.json")
    assert all(BASE.sha(directory / name) == stamp for name, stamp in manifest.items())
    assert E.read(directory / "clarification-lock.json") == pins()
    t = AutoTokenizer.from_pretrained(BASE.MODEL, local_files_only=True)
    eos = t.convert_tokens_to_ids("<|im_end|>")
    responses, token_trace = [[json.loads(line) for line in (directory / file).read_text().splitlines()]
                              for file in ("responses.jsonl", "tokens.jsonl")]
    for req, replay, trace in zip(requests(), responses, token_trace, strict=True):
        assert replay["id"] == req["id"] and replay["response"] == trace["response"]
        assert trace["input_ids"] == BASE.prompt(t, req)
        ids = trace["output_ids"]
        assert ids and len(ids) <= req["max_output_tokens"] and eos not in ids[:-1]
        assert (ids[-1] == eos) == (replay["response"]["termination"] == "complete")
        assert t.decode(ids, skip_special_tokens=True).strip() == replay["response"]["text"]
    return {"verified_calls": len(responses), "episodes": len(responses)//2, "optimizer_updates": 0}


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode", choices=("deck", "run", "verify"))
    p.add_argument("--directory", type=Path, default=HERE / "evidence")
    args = p.parse_args()
    if args.mode == "deck":
        E.emit(requests())
    elif args.mode == "run":
        with patch.object(BASE.suite, "collect", collect):
            BASE.run(args.directory)
    else:
        E.emit(verify(args.directory))
