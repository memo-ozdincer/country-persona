"""Verify native receipts and score the final UNIFIL records."""
import argparse
from hashlib import sha256
from importlib.util import module_from_spec, spec_from_file_location
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = spec_from_file_location("unifil_live_route", HERE / "live.py")
m = module_from_spec(spec)
spec.loader.exec_module(m)
e, D = m.e, m.D
HEADER = (
    "On 31 August 2023 the Security Council adopted France’s draft S/2023/641 as resolution 2695 (2023), "
    "13–0–2, with China and Russia abstaining. The resolution extended the existing UNIFIL mandate through "
    "31 August 2024. It reaffirmed independent performance of mandated tasks without prior permission and "
    "continued coordination with Lebanon’s Government under the status-of-forces agreement."
)
CONTRAST = (
    "Both Brazil and China supported UNIFIL’s work. Brazil said the text addressed some Lebanese concerns, "
    "while China said it did not fully address them."
)


def read_lines(file):
    return [json.loads(line) for line in (m.RUN / file).read_text().splitlines()]


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def verify():
    from jinja2.sandbox import ImmutableSandboxedEnvironment
    from tokenizers import Tokenizer

    pinned = e.read(m.RUN / "complete.json")
    assert set(pinned) == {"calls.jsonl", "trace.jsonl", "tokens.jsonl", "inputs.json", "launch.json"}
    assert all(digest(m.RUN / name) == expected for name, expected in pinned.items())
    assert m.pins() == e.read(m.RUN / "inputs.json")
    release = e.read(e.HERE / "release.json")
    assert release["version"] == "1.2"
    assert all(digest(e.HERE / name) == value for name, value in release["sha256"].items())
    launch = e.read(m.RUN / "launch.json")
    assert launch["gpu_name"] == "NVIDIA RTX PRO 6000 Blackwell Server Edition" and launch["optimizer_updates"] == 0
    checkpoint = Path(launch["checkpoint"])
    assert digest(checkpoint / "model.safetensors.index.json") == launch["checkpoint_index_sha256"]
    tokenizer = Tokenizer.from_file(str(checkpoint / "tokenizer.json"))
    template = ImmutableSandboxedEnvironment(trim_blocks=True, lstrip_blocks=True).from_string(
        (checkpoint / "chat_template.jinja").read_text())
    eos = tokenizer.token_to_id("<|im_end|>")
    zipped = iter(zip(read_lines("calls.jsonl"), read_lines("tokens.jsonl"), strict=True))
    context, inventory, plan = m.select()
    assert e.read(HERE / "plan.json") == plan
    calls = 0

    def generate(req):
        nonlocal calls
        calls += 1
        record, tokens = next(zipped)
        assert req == record["request"] and record["reply"] == tokens["response"]
        rendered = template.render(messages=req["messages"], enable_thinking=False,
                                   add_generation_prompt=True, tools=None)
        inp = tokenizer.encode(rendered, add_special_tokens=False).ids
        reply, out = tokens["response"], tokens["output_ids"]
        assert inp == tokens["input_ids"] and len(inp) == reply["input_tokens"]
        assert out and eos not in out[:-1] and len(out) == reply["output_tokens"] <= req["max_output_tokens"]
        assert (out[-1] == eos) == (reply["termination"] == "complete")
        assert tokenizer.decode(out, skip_special_tokens=True).strip() == reply["text"]
        return reply

    assert list(m.simulate(context, inventory, generate)) == read_lines("trace.jsonl")
    assert next(zipped, None) is None and calls <= m.LIMIT
    return {"calls": calls, "arms": len(m.ARMS), "full_native_trace": True, "optimizer_updates": 0}


def deck(form='exact'):
    source = m.model_inputs()[0]
    case = {"id": "unifil-live", "track": "record", "word_cap": 150, "task": source["task"],
            "rubric": source["rubric"], "public": source["evidence"], "owned": []}
    blocks = {block["id"]: block["text"] for block in source["evidence"]}
    if form == "compact":
        blocks = blocks | e.read(HERE / "compact.json")
    output = {}
    for path in read_lines("trace.jsonl"):
        mask = path["final_mask"]
        evidence = [block for i, block in enumerate(m.NAMES) if mask & m.bit(i)]
        lines = [HEADER, *(blocks[key] for key in evidence)]
        if {"brazil", "china"} <= set(evidence):
            lines.append(CONTRAST)
        text = "\n\n".join(lines)
        assert text.strip()
        calls = [{}, {}, {"text": text, "termination": "complete"}]
        packet = e.final_packet(case, calls)
        output[path["arm"]] = {"sources_delivered": evidence, "record": packet, "cost": path["cost"]}
    return case, output


def score(form="exact"):
    case, packets = deck(form)
    marks = e.read(HERE / "marks.json")
    assert set(marks) == {row["record"]["id"] for row in packets.values()}
    result = {}
    for arm, data in packets.items():
        record = data["record"]
        score = e.final_score(case, [{}, {}, {"text": record["answer"], "termination": "complete"}], marks[record["id"]])
        result[arm] = {"released": score["released_70"], "words": score["words"],
                       "cost": data["cost"], "net": score["released_70"] - data["cost"],
                       "source_guard": score["guard"], "delivered": data["sources_delivered"]}
    return result


def stress():
    # Deterministically replay drop and source-mismatch branches without a native call.
    context, pair, plan = m.select()
    canonical = {row["arm"]: row for row in m.simulate(context, pair, m.ideal)}

    def corrupt(req):
        result = m.ideal(req)
        payload = json.loads(req["messages"][-1]["content"])
        if payload["desk"] == "second_reply" and payload["card"] == "russia":
            result["text"] = '{"card":"russia","quote":"The Council rejected the renewal."}'
        return result

    altered = {row["arm"]: row for row in m.simulate(context, pair, corrupt)}
    assert altered["learned"]["final_mask"] == canonical["no_request"]["final_mask"]
    assert altered["learned"]["followup"]["admitted"] is False
    assert altered["learned"]["cost"] == canonical["learned"]["cost"]
    return {"rejected_followup_mask": altered["learned"]["final_mask"],
            "planned_authenticated_mask": canonical["learned"]["final_mask"], "plan": plan}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("verify", "packets", "score", "stress"))
    mode = parser.parse_args().mode
    e.emit({"verify": verify, "packets": lambda: deck()[1], "score": score, "stress": stress}[mode]())
