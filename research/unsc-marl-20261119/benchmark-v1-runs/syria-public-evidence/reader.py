"""Frozen request collection for a source-local workshop evidence reader."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import sys
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
BASE = HERE.parent / "syria-baseline"
PROJECTED = HERE.parent / "syria-constraint-transport"
sys.path.insert(0, str(BASE))
import collect as baseline
import review

E = baseline.suite.e
BR, UK = "Brazil workshop delegate", "United Kingdom workshop delegate"
FIELDS = {"duration": ["nine", "six"], "checkpoint": ["additional"]}
STRESS = (
    (BR, "My fictional Brazil mandate requires nine months.", ("duration", "nine")),
    (BR, "The historical draft called for nine months.", None),
    (UK, "My fictional UK mandate requires a six-month duration.", ("duration", "six")),
    (UK, "I am proposing a six-month duration for discussion.", None),
    (UK, "The UK's fictional constraint mandates an additional checkpoint.", ("checkpoint", "additional")),
    (UK, "The UK's fictional constraint does not mandate an additional checkpoint.", None),
    (BR, "The nine-month duration is a binding condition for my Brazil workshop mandate.", ("duration", "nine")),
    (BR, "The nine-month duration is a binding condition for the UK workshop mandate.", None),
)


def pair_inputs():
    new = {r["episode"]: r for r in E.read(PROJECTED / "evidence/episodes.json")}
    for key, case, arm, _, calls in review.episodes():
        if arm != "peer":
            continue
        raw = [(c["speaker"], c["text"]) for c in calls[:2]]
        row = new[key]
        projected = [(calls[0]["speaker"], row["projected_text"]),
                     (calls[1]["speaker"], row["note"]["response"]["text"])]
        yield key + "/raw", case, raw
        yield key + "/projected", case, projected


def note_id(speaker, text):
    return "note-" + E.checksum([speaker, text])[:16]


def deck():
    source = {}
    menu = next(iter(baseline.roster().values()))["options"]
    for _, _, notes in pair_inputs():
        for speaker, text in notes:
            source[note_id(speaker, text)] = (speaker, text)
    archived = len(source)
    for speaker, text, _ in STRESS:
        source[note_id(speaker, text)] = (speaker, text)
    assert len(source) == archived + len(STRESS)
    instruction = (
        'Extract only the actual author\'s own positive fictional workshop requirement and explicitly endorsed '
        'package from the note. Never infer a requirement from the historical vote, a suggested package, an '
        'explicitly negated claim, a peer\'s mandate, or what could be discussed. Copy a short exact quote containing '
        'the relevant meaning, including the reason it is binding or endorsed. If absent, use null. A proposal '
        'can be an endorsement if the author explicitly recommends a specific package or its distinctive terms. '
        'Keep the requirement even if the author also endorses a package that contradicts it. '
        'Return one JSON object with exactly two keys. "constraint" is null or '
        '{"field":"duration or checkpoint","value":"nine, six or additional","quote":"exact text"}. '
        '"endorsement" is null or {"option":"A, B, C or D","quote":"exact text"}. '
        'Output JSON only.'
    )
    return [{
        "id": key, "max_output_tokens": 220,
        "messages": [{"role": "system", "content": instruction}, {"role": "user", "content": json.dumps({
            "speaker": speaker, "note": text, "field_dictionary": FIELDS,
            "packages": [{"option": p["id"], "text": p["text"]} for p in menu],
        }, ensure_ascii=False)}],
    } for key, (speaker, text) in sorted(source.items())]


def pins():
    files = (Path(__file__).resolve(), HERE / "protocol.md", HERE / "requests.json", E.HERE / "release.json",
             BASE / "evidence/complete.json", PROJECTED / "evidence/complete.json")
    return {str(p.relative_to(HERE.parent.parent)): baseline.sha(p) for p in files}


def collect(generate, directory):
    requests = E.read(HERE / "requests.json")
    assert requests == deck()
    for request in requests:
        baseline.suite.append(directory / "extractions.jsonl", {"request": request, "response": generate(request)})
    (directory / "reader-lock.json").write_text(json.dumps(pins(), indent=2) + "\n")


def verify(directory):
    from transformers import AutoTokenizer

    assert all(baseline.sha(directory / name) == stamp for name, stamp in E.read(directory / "complete.json").items())
    assert E.read(directory / "reader-lock.json") == pins()
    t = AutoTokenizer.from_pretrained(baseline.MODEL, local_files_only=True)
    eos = t.convert_tokens_to_ids("<|im_end|>")
    traces, tokens = ([json.loads(line) for line in (directory / file).read_text().splitlines()] for file in (
        "extractions.jsonl", "tokens.jsonl"))
    assert deck() == E.read(HERE / "requests.json")
    for expected, row, trace in zip(deck(), traces, tokens, strict=True):
        request = row["request"]
        assert request == expected and row["response"] == trace["response"]
        assert trace["input_ids"] == baseline.prompt(t, request)
        ids = trace["output_ids"]
        assert len(ids) <= request["max_output_tokens"] and eos not in ids[:-1]
        assert bool(ids and ids[-1] == eos) == (row["response"]["termination"] == "complete")
        assert t.decode(ids, skip_special_tokens=True).strip() == row["response"]["text"]
    return {"verified_calls": len(traces), "capped": sum(r["response"]["termination"] == "cap" for r in traces),
            "stress_notes": len(STRESS), "archived_note_pairs": sum(1 for _ in pair_inputs())}


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode", choices=("deck", "run", "verify"))
    p.add_argument("--directory", type=Path, default=HERE / "evidence")
    args = p.parse_args()
    if args.mode == "deck":
        E.emit(deck())
    elif args.mode == "run":
        with patch.object(baseline.suite, "collect", collect):
            baseline.run(args.directory)
    else:
        E.emit(verify(args.directory))
