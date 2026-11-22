"""Capture the two missing-rationale scope probes with the frozen reader."""
import argparse
import json
from pathlib import Path
from unittest.mock import patch

import documentary as doc
import held

HERE, OUT, e = doc.HERE, doc.HERE / "supplement-evidence", doc.e
SOURCE = held.BLOCK["algeria"]["text"]
WITNESS = ("Algeria attributed its abstention to concerns over implementation of resolution 2722 (2024) "
           "and what it regarded as misuse or misinterpretation of self-defence through attacks on sovereign countries’ territory.")
ROWS = [
    {"id": "algeria-full-rationale", "expected": "supports", "source": "algeria", "witness": WITNESS,
     "assertion": "Algeria abstained over implementation of resolution 2722 (2024) and perceived misuse or misinterpretation of self-defence in attacks on sovereign countries’ territory."},
    {"id": "algeria-own-territory", "expected": "unknown", "source": "algeria", "witness": WITNESS,
     "assertion": "Algeria said its abstention was prompted by attacks on Algeria’s own territory."},
]


def queries():
    assert SOURCE.count(WITNESS) == 1
    for row in ROWS:
        payload = {"quoted_premise": row["witness"], "passage_for_references": SOURCE,
                   "assertion": row["assertion"]}
        for item in held.archived.protocol.encoded(("supplement", row["id"]), held.archived.TASK,
                                                   payload, held.archived.OPTIONS):
            yield item | {"observation": list(item["observation"]), "legal": list(item["legal"]),
                          "max_output_tokens": 2}


def plan():
    files = (Path(__file__), HERE / "supplement-protocol.md", HERE / "results.json",
             Path(held.__file__), doc.ADMISSION / "plan.json", doc.ADMISSION / "fit.json")
    return {"probes": ROWS, "requests": list(queries()),
            "sha256": {str(p.relative_to(doc.team.STUDY)): doc.hash_bytes(p) for p in files}}


def lock():
    assert plan() == e.read(HERE / "supplement-plan.json")


def run():
    with patch.multiple(held, lock=lock, asks=queries, HERE=HERE, OUT=OUT):
        # The base launch records protocol.md. Supplement-specific inputs have their own plan.
        held.run()


def verify():
    from transformers import AutoTokenizer

    lock()
    manifest = e.read(OUT / "complete.json")
    assert set(manifest) == {"calls.jsonl", "tokens.jsonl", "launch.json"}
    assert all(doc.hash_bytes(OUT / name) == digest for name, digest in manifest.items())
    receipt = e.read(OUT / "launch.json")
    assert receipt["cases"] == [doc.CASE["id"]] and receipt["optimizer_updates"] == 0
    assert receipt["release_sha256"] == doc.hash_bytes(doc.RELEASE / "release.json")
    assert receipt["protocol_sha256"] == doc.hash_bytes(HERE / "protocol.md")
    assert receipt["checkpoint_index_sha256"] == held.report.plan()["checkpoint_index_sha256"]
    tok = AutoTokenizer.from_pretrained(held.base.MODEL, local_files_only=True)
    options, eos = held.ids(tok), tok.convert_tokens_to_ids("<|im_end|>")
    calls, traces = ([json.loads(line) for line in (OUT / f).read_text().splitlines()]
                     for f in ("calls.jsonl", "tokens.jsonl"))
    checked = []
    for expected, actual, trace in zip(queries(), calls, traces, strict=True):
        assert all(actual[key] == v for key, v in expected.items())
        assert trace["input_ids"] == held.base.prompt(tok, expected) and trace["response"] == actual["reply"]
        assert len(trace["input_ids"]) == actual["reply"]["input_tokens"]
        pick = max(range(3), key=actual["scores"].__getitem__)
        assert trace["output_ids"] == [options[pick], eos] and actual["reply"]["text"] == "ABC"[pick]
        assert 0 <= actual["legal_mass"] <= 1
        checked.append({"observation": expected["observation"], "scores": actual["scores"]})
    assert len(checked) == 4
    return {"checks": checked, "evidence_sha256": manifest}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("plan", "run", "verify"))
    mode = parser.parse_args().mode
    if mode == "run":
        run()
    else:
        e.emit({"plan": plan, "verify": verify}[mode]())
