"""Generate source-scoped chair fragments and assemble received paragraphs."""
import argparse
import json
from pathlib import Path
import sys
from time import perf_counter
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
PARENT = HERE.parent
sys.path.insert(0, str(PARENT))
import live_tolerance as old
from assemble import CONNECTIVE

base, prior, frozen, CASE, READ = old.base, old.prior, old.frozen, old.CASE, old.READ
OUT = HERE / "evidence"
PUBLIC = ("Write one compact public Council record paragraph in at most 46 words. "
          "Preserve draft and adopted symbols, both sponsors and the voting outcome. "
          "State what was urged publicly and its legal limit. Preserve the actor, "
          "public oral form, recipient and date of the requested briefing. "
          "Use only the supplied public blocks and return the paragraph alone.")
NATIONAL = ("Write one attributed paragraph in at most 40 words. "
            "Use only this delegation's note. Preserve the distinct claims, reasons "
            "and qualifications. Keep independent concerns about different objects "
            "separate. Never attach one objection to an instrument mentioned in another. "
            "Drop filler before dropping a specific fact. Return the paragraph alone.")


def notes():
    records = READ(PARENT / "verified.json")["records"]
    selected = [records["note/" + role] for role in CASE["roles"]]
    assert all(row["termination"] == "complete" for row in selected)
    return [row["text"] for row in selected]


def requests():
    result = [old.request("public", PUBLIC, {"public": frozen.visible_blocks(CASE["public"])}, 102)]
    result.extend(old.request(f"role-{index}", NATIONAL, {"role": role, "note": note}, 62)
                  for index, (role, note) in enumerate(zip(CASE["roles"], notes(), strict=True)))
    assert sum(row["max_output_tokens"] for row in result) == 288
    return result


def plan():
    pins = (Path(__file__), HERE / "protocol.md", PARENT / "docket.json", PARENT / "verified.json",
            PARENT / "assemble.py", old.prior.RELEASE / "release.json", Path(base.__file__))
    return {"requests": requests(), "sha256": {str(p.relative_to(prior.STUDY)): prior.digest(p) for p in pins}}


def collect(generate, directory):
    for request in requests():
        start = perf_counter()
        out = generate(request)
        prior.append(directory / "calls.jsonl", {"request": request, "response": out,
                                                 "elapsed_seconds": perf_counter() - start})


def run():
    assert plan() == READ(HERE / "plan.json")
    with patch.object(base.suite, "collect", collect), patch.object(
            base, "roster", return_value={CASE["id"]: CASE}), patch.object(
            base, "HERE", HERE), patch.object(base.suite.e, "HERE", prior.RELEASE):
        base.run(OUT)


def compose(fragments):
    public = fragments["public"]
    scoped = [fragments[f"role-{i}"] for i in range(3)]
    verbatim = [{"text": note, "termination": "complete"} for note in notes()]
    records, packets = {}, {}
    for name, roles in (("scoped", scoped), ("verbatim", verbatim)):
        for mask in range(8):
            parts = [public]
            for bit, role in enumerate(roles):
                if mask & (1 << bit):
                    if bit == 2 and mask & 3:
                        parts.append({"text": CONNECTIVE, "termination": "complete"})
                    parts.append(role)
            answer = "\n\n".join(part["text"] for part in parts)
            statuses = {part["termination"] for part in parts if part["text"]} | {
                "error" for part in parts if not part["text"].strip()}
            termination = "error" if "error" in statuses else "cap" if "cap" in statuses else "complete"
            record = {"text": answer, "termination": termination}
            records[f"{name}/mask-{mask}"] = record
            packet = frozen.final_packet(CASE, [{}, {}, record])
            packets[packet["id"]] = frozen.judge.request(packet)
    return records, dict(sorted(packets.items()))


def verify():
    from transformers import AutoTokenizer

    assert plan() == READ(HERE / "plan.json")
    manifest = READ(OUT / "complete.json")
    assert set(manifest) == {"launch.json", "calls.jsonl", "tokens.jsonl"}
    assert all(prior.digest(OUT / name) == val for name, val in manifest.items())
    launch = READ(OUT / "launch.json")
    assert launch["cases"] == [CASE["id"]] and launch["optimizer_updates"] == 0
    assert launch["protocol_sha256"] == prior.digest(HERE / "protocol.md")
    assert launch["checkpoint_index_sha256"] == prior.digest(base.MODEL / "model.safetensors.index.json")
    assert launch["release_sha256"] == prior.digest(prior.RELEASE / "release.json")
    tokenizer = AutoTokenizer.from_pretrained(base.MODEL, local_files_only=True)
    eos = tokenizer.convert_tokens_to_ids("<|im_end|>")
    calls, tokens = [prior.wire.n.lines(OUT / file) for file in ("calls.jsonl", "tokens.jsonl")]
    fragments = {}
    for req, row, trace in zip(requests(), calls, tokens, strict=True):
        out = row["response"]
        assert row["request"] == req and trace["input_ids"] == base.prompt(tokenizer, req)
        assert trace["response"] == out and len(trace["output_ids"]) == out["output_tokens"]
        assert tokenizer.decode(trace["output_ids"], skip_special_tokens=True).strip() == out["text"]
        assert bool(trace["output_ids"] and trace["output_ids"][-1] == eos) == (out["termination"] == "complete")
        fragments[req["id"]] = out | {"elapsed_seconds": row["elapsed_seconds"]}
    records, packets = compose(fragments)
    return {"fragments": fragments, "records": records, "blind_packets": packets, "evidence_sha256": manifest}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("plan", "run", "verify"))
    mode = parser.parse_args().mode
    if mode == "run":
        run()
    else:
        frozen.emit({"plan": plan, "verify": verify}[mode]())
