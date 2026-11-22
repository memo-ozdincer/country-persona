"""Replay Cyprus model tokens and apply the frozen source-grounded rubric."""
import argparse
import json
from pathlib import Path

import transfer as t
import review_witness as shared

e = shared.e
HERE = Path(__file__).resolve().parent


def rows(name):
    return [json.loads(line) for line in (t.RUN / name).read_text().splitlines()]


def verify():
    from jinja2.sandbox import ImmutableSandboxedEnvironment
    from tokenizers import Tokenizer

    digest = shared.digest
    assert t.pins() == e.read(t.RUN / "inputs.json")
    pins = e.read(t.RUN / "complete.json")
    assert set(pins) == {"launch.json", "trace.jsonl", "inputs.json", "tokens.jsonl"}
    assert all(digest(t.RUN / name) == value for name, value in pins.items())
    launch = e.read(t.RUN / "launch.json")
    release = e.read(shared.RELEASE / "release.json")
    assert digest(Path(e.judge.__file__)) == release["sha256"]["judge_score.py"]
    assert all(digest(shared.RELEASE / name) == value for name, value in release["sha256"].items())
    model = Path(launch["checkpoint"])
    assert launch["optimizer_updates"] == 0 and launch["gpu_name"] == "NVIDIA RTX PRO 6000 Blackwell Server Edition"
    assert digest(model / "model.safetensors.index.json") == launch["checkpoint_index_sha256"]
    template = ImmutableSandboxedEnvironment(trim_blocks=True, lstrip_blocks=True).from_string(
        (model / "chat_template.jinja").read_text())
    tok = Tokenizer.from_file(str(model / "tokenizer.json"))
    eos = tok.token_to_id("<|im_end|>")
    trace = rows("trace.jsonl")
    actual = (line for line in trace if "request" in line)
    receipts = iter(zip(actual, rows("tokens.jsonl"), strict=True))

    def replay(req):
        saved, native = next(receipts)
        reply = saved["reply"]
        assert req == saved["request"] and reply == native["response"]
        rendered = template.render(messages=req["messages"], add_generation_prompt=True,
                                   enable_thinking=False, tools=None)
        inp, out = native["input_ids"], native["output_ids"]
        assert inp == tok.encode(rendered, add_special_tokens=False).ids and len(inp) == reply["input_tokens"]
        assert out and len(out) == reply["output_tokens"] <= req["max_output_tokens"] and eos not in out[:-1]
        assert (out[-1] == eos) == (reply["termination"] == "complete")
        assert tok.decode(out, skip_special_tokens=True).strip() == reply["text"]
        return reply

    assert json.loads(json.dumps(list(t.execute(replay)))) == trace
    assert next(receipts, None) is None
    delegate_rows = [row for row in trace if row["stage"] == "delegate"]
    return {"questions": len(delegate_rows), "admitted_signs": sum(r.get("accepted", False) for r in delegate_rows),
            "physical_calls": len(rows("tokens.jsonl")), "optimizer_updates": launch["optimizer_updates"]}


def render(case, menu, state):
    decision = t.game.terminal(menu, state)[0]
    text = (f"Decision: {decision}\n\nFictional briefing. "
            + t.common.renderer.public_conditions(case, state) + " " + t.proof(case, state))
    return text + (
        "\n\nOn 30 January 2023 the Council unanimously adopted the UK draft S/2023/64, "
        "15–0–0, as resolution 2674 (2023). It extended UNFICYP through 31 January 2024 and "
        "expressed readiness for a six-month implementation review. The Council President "
        "reported that the parties maintained their positions. Council unanimity did not "
        "establish a party settlement. The Council reaffirmed the bicommunal, bizonal federation "
        "framework with political equality. UNFICYP's mandated authority extends throughout Cyprus. "
        "This fictional briefing choice does not change the mandate, resolution or party positions."
    )


def deck():
    case, menu, _, _ = t.setup()
    writers = [row for row in rows("trace.jsonl") if row["stage"] == "writer"]
    assert [row["arm"] for row in writers] == ["raw", "proof"] and writers[0]["state"] == writers[1]["state"]
    state = writers[0]["state"]
    choice = t.game.terminal(menu, t.selected())[0]
    sources = t.public(case, state) + [{"id": "checked-exclusions", "text": t.proof(case, state)}]
    public_case = {"id": "cyprus-transfer", "track": "workshop", "word_cap": 150, "gold": [choice],
                   "task": t.TASK, "rubric": case["rubric"], "public": sources, "owned": []}
    drafts = {row["arm"]: row["reply"] for row in writers}
    drafts["compiled"] = {"text": render(case, menu, state), "termination": "complete"}
    calls = {name: [{}, {}, reply] for name, reply in drafts.items()}
    return {name: (public_case, events, e.final_packet(public_case, events)) for name, events in calls.items()}


def score(records):
    marks = e.read(HERE / "marks.json")
    assert set(marks) == {item[2]["id"] for item in records.values()}
    return {name: e.final_score(case, calls, marks[packet["id"]])
            for name, (case, calls, packet) in records.items()}


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode", choices=("verify", "packets", "score"))
    mode = p.parse_args().mode
    if mode == "verify":
        e.emit(verify())
    else:
        records = deck()
        e.emit(score(records) if mode == "score" else {name: item[2] for name, item in records.items()})
