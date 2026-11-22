"""Generate the locked 2739 chair counterfactuals from paired note edits."""
import argparse
from importlib.util import module_from_spec, spec_from_file_location
from itertools import product
import json
from pathlib import Path
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
PARENT = HERE.parent
OLD = PARENT / "source-check"
spec = spec_from_file_location("source_check_for_correction", OLD / "source_check.py")
source = module_from_spec(spec)
spec.loader.exec_module(source)
study, e, CASE, base, suite = source.study, source.e, source.CASE, source.base, source.suite
OUT = HERE / "evidence"

REMOVE = (
    " Positions overlapped on reporting extension but differed on Houthi cessation demands",
    " Positions overlapped on reporting limits but differed on military authorization;",
)
REPLIES = (
    "Algeria valued monthly reporting on attacks on merchant and commercial vessels to keep the Council informed. "
    "It abstained over implementation of resolution 2722 and alleged misuse or misinterpretation of self-defence "
    "through attacks on sovereign territory. This does not establish Algeria's endorsement of the extension or its deadline.",
    "Japan and the United States supported the extension so the Council would have accurate and timely information "
    "on the attacks for future deliberations. Both voted in favour. Their explanation gives an informational rationale "
    "and establishes no sponsors' position on military authorization.",
)


def arms():
    old = e.read(OLD / "verified.json")["traces"]
    for order in (0, 1):
        archive = old[f"peer/{order}"]
        opening, reply = archive["opening"], archive["second"]["reply"]
        assert opening["text"].endswith(REMOVE[order])
        assert len(REPLIES[order].split()) <= 55
        for remove, revise in product((0, 1), repeat=2):
            notes = [
                {"speaker": opening["speaker"], "text": opening["text"].removesuffix(REMOVE[order])
                 if remove else opening["text"]},
                {"speaker": archive["second"]["request"]["speaker"],
                 "text": REPLIES[order] if revise else reply["text"]},
            ]
            request = e.build_request(CASE, "peer", order, notes)
            original = archive["final"]["request"]
            original_payload = json.loads(original["messages"][1]["content"])
            new_payload = json.loads(request["messages"][1]["content"])
            assert original_payload | {"notes": new_payload["notes"]} == new_payload
            assert original["messages"][:1] == request["messages"][:1]
            assert original | {"messages": request["messages"]} == request
            yield f"{order}/{remove}{revise}", request, archive["final"]["reply"] if not (remove or revise) else None


def plan():
    source.lock()
    files = (Path(__file__), HERE / "protocol.md", PARENT / "docket.json", OLD / "plan.json",
             OLD / "verified.json", OLD / "results.json", OLD / "source_check.py", Path(base.__file__),
             study.RELEASE / "release.json")
    return {"requests": {key: request for key, request, _ in arms()},
            "reused": ["0/00", "1/00"], "physical_calls": 6,
            "sha256": {str(path.relative_to(study.RELEASE.parent)): study.pin(path) for path in files}}


def locked():
    assert plan() == e.read(HERE / "plan.json")


def collect(generate, directory):
    for key, request, archived in arms():
        if archived is None:
            reply = generate(request)
            source.append(directory / "calls.jsonl", {"id": key, "request": request, "reply": reply})


def run():
    locked()
    with patch.object(base, "roster", return_value={CASE["id"]: CASE}), patch.object(
        base, "HERE", HERE
    ), patch.object(suite, "collect", collect):
        base.run(OUT)


def verify():
    from transformers import AutoTokenizer

    locked()
    manifest = e.read(OUT / "complete.json")
    assert set(manifest) == {"launch.json", "calls.jsonl", "tokens.jsonl"}
    assert all(study.pin(OUT / key) == digest for key, digest in manifest.items())
    launch = e.read(OUT / "launch.json")
    assert launch["optimizer_updates"] == 0 and launch["cases"] == [CASE["id"]]
    assert launch["protocol_sha256"] == study.pin(HERE / "protocol.md")
    assert launch["release_sha256"] == study.pin(study.RELEASE / "release.json")
    assert launch["collector_sha256"] == study.pin(Path(base.__file__))
    assert launch["checkpoint_index_sha256"] == study.plan()["checkpoint_index_sha256"]
    records = [json.loads(line) for line in (OUT / "calls.jsonl").read_text().splitlines()]
    traces = [json.loads(line) for line in (OUT / "tokens.jsonl").read_text().splitlines()]
    assert len(records) == len(traces) == 6
    tok = AutoTokenizer.from_pretrained(base.MODEL, local_files_only=True)
    eos = tok.convert_tokens_to_ids("<|im_end|>")
    live = iter(zip(records, traces, strict=True))
    packets, outcomes = {}, {}
    for key, request, old in arms():
        if old is None:
            row, trace = next(live)
            assert row["id"] == key and row["request"] == request
            reply = row["reply"]
            assert trace["response"] == reply and trace["input_ids"] == base.prompt(tok, request)
            assert len(trace["input_ids"]) == reply["input_tokens"]
            assert len(trace["output_ids"]) == reply["output_tokens"]
            assert tok.decode(trace["output_ids"], skip_special_tokens=True).strip() == reply["text"]
            assert bool(trace["output_ids"] and trace["output_ids"][-1] == eos) == (reply["termination"] == "complete")
        else:
            reply = old
        packet = e.judge.request(e.final_packet(CASE, [{}, {}, reply]))
        packets[packet["id"]] = packet
        outcomes[key] = {"request": request, "reply": reply, "packet": packet["id"], "reused": old is not None}
    assert next(live, None) is None
    return {"packets": dict(sorted(packets.items())), "outcomes": outcomes, "sha256": manifest}


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode", choices=("plan", "run", "verify"))
    mode = p.parse_args().mode
    if mode == "run":
        run()
    else:
        e.emit({"plan": plan, "verify": verify}[mode]())
