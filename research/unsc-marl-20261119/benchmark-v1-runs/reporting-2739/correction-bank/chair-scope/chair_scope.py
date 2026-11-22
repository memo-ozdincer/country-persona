"""Replay the eight fixed 2739 note pairs with an attribution-scoped chair."""
import argparse
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

from unittest.mock import patch
import json

HERE = Path(__file__).resolve().parent
BANK = HERE.parent
spec = spec_from_file_location("historical_correction_bank", BANK / "correction.py")
bank = module_from_spec(spec)
spec.loader.exec_module(bank)
base, e, CASE, suite = bank.base, bank.e, bank.CASE, bank.suite
pin = bank.study.pin
OUT = HERE / "evidence"

INSTRUCTION = (
    "Use public source blocks for the adopted document, vote and operative action, "
    "preserving paragraph numbers and dates. In each delegation's explanation, use only "
    "its own desk note for its stated position and reason. Separate the text's legal scope "
    "from positions delegates express. Compare the two explanations only on a specific "
    "proposition supported by both of their own notes. If support comes from only one "
    "desk or is missing, leave that comparison unverified. Treat an abstention as a vote "
    "on the whole text. Describe silence as an evidence gap. Write one concise record "
    "within the task's word limit."
)


def cases():
    archive = e.read(BANK / "verified.json")["outcomes"]
    for key, row in archive.items():
        original = row["request"]
        request = original | {"messages": [
            {"role": "system", "content": original["messages"][0]["content"] + " " + INSTRUCTION},
            *original["messages"][1:]
        ]}
        assert request["max_output_tokens"] == 280
        yield key, request


def plan():
    bank.locked()
    files = (Path(__file__), HERE / "protocol.md", BANK / "plan.json", BANK / "verified.json",
             BANK / "results.json", BANK / "correction.py", BANK / "final-marks.json",
             Path(base.__file__), bank.study.RELEASE / "release.json")
    return {"requests": dict(cases()), "physical_calls": 8,
            "sha256": {str(path.relative_to(bank.study.RELEASE.parent)): pin(path) for path in files}}


def lock():
    assert plan() == e.read(HERE / "plan.json")


def collect(generate, directory):
    for key, request in cases():
        reply = generate(request)
        bank.source.append(directory / "calls.jsonl", {"id": key, "request": request, "reply": reply})


def run():
    lock()
    with patch.object(base, "roster", return_value={CASE["id"]: CASE}), patch.object(
        base, "HERE", HERE
    ), patch.object(suite, "collect", collect):
        base.run(OUT)


def verify():
    from transformers import AutoTokenizer

    lock()
    manifest = e.read(OUT / "complete.json")
    assert set(manifest) == {"calls.jsonl", "launch.json", "tokens.jsonl"}
    assert all(pin(OUT / name) == digest for name, digest in manifest.items())
    launch = e.read(OUT / "launch.json")
    assert launch["cases"] == [CASE["id"]] and launch["optimizer_updates"] == 0
    assert launch["protocol_sha256"] == pin(HERE / "protocol.md")
    assert launch["release_sha256"] == pin(bank.study.RELEASE / "release.json")
    assert launch["collector_sha256"] == pin(Path(base.__file__))
    assert launch["checkpoint_index_sha256"] == bank.study.plan()["checkpoint_index_sha256"]
    tok = AutoTokenizer.from_pretrained(base.MODEL, local_files_only=True)
    eos = tok.convert_tokens_to_ids("<|im_end|>")
    records, token_rows = ([json.loads(line) for line in (OUT / name).read_text().splitlines()]
                           for name in ("calls.jsonl", "tokens.jsonl"))
    packets, mapping = {}, {}
    for (key, request), actual, row in zip(cases(), records, token_rows, strict=True):
        reply = actual["reply"]
        assert actual["id"] == key and request == actual["request"]
        assert row["input_ids"] == base.prompt(tok, request) and row["response"] == reply
        assert len(row["input_ids"]) == reply["input_tokens"]
        assert len(row["output_ids"]) == reply["output_tokens"] <= 280
        assert tok.decode(row["output_ids"], skip_special_tokens=True).strip() == reply["text"]
        assert bool(row["output_ids"] and row["output_ids"][-1] == eos) == (reply["termination"] == "complete")
        packet = e.judge.request(e.final_packet(CASE, [{}, {}, reply]))
        packets[packet["id"]] = packet
        mapping[key] = {"packet": packet["id"], "reply": reply}
    assert len(mapping) == 8
    return {"packets": dict(sorted(packets.items())), "outcomes": mapping, "sha256": manifest}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("plan", "run", "verify"))
    mode = parser.parse_args().mode
    if mode == "run":
        run()
    else:
        e.emit({"plan": plan, "verify": verify}[mode]())
