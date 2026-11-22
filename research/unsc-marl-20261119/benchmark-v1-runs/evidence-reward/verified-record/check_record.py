"""Verify native selection and score the composed records under benchmark v1.2."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
from unittest.mock import patch

import record as r

HERE = Path(__file__).resolve().parent
e = r.e


def rows(name):
    return [json.loads(line) for line in (r.RUN / name).read_text().splitlines()]


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def software():
    by_arm = {}
    for arm in r.ARMS:
        columns = r.fields(arm)
        correct = r.direct(arm)
        _, _, baseline = r.compose(arm, correct)
        withheld = arm == "cyprus-withheld"
        assert sum(status == "admitted" for status in baseline.values()) == (3 if withheld else 4)
        for column in columns:
            key = column["id"]
            if baseline[key] == "missing_source":
                assert r.admit(arm, correct | {key: r.direct("cyprus")[key]})[1][key] == "missing_source"
                continue
            candidate = correct[key]
            assert candidate
            _, plausible = r.admit(arm, correct | {key: candidate + " Invented tally: 18 in favour."})
            assert plausible[key] == "not_exact_for_source"
            copied_from_other_source = next(correct[another["id"]] for another in columns
                                            if another["id"] != key and correct[another["id"]])
            assert r.admit(arm, correct | {key: copied_from_other_source})[1][key] == "not_exact_for_source"
            fragment = candidate.split()[0]
            assert r.admit(arm, correct | {key: fragment})[1][key] == "field_coverage_missing"
        _, blocked = r.admit(arm, r.parse({"text": "not JSON", "termination": "complete"}))
        assert all(x != "admitted" for x in blocked.values())
        by_arm[arm] = {"direct_fields": baseline, "malformed_fields_admitted": 0}
    forged = r.direct("cyprus")["vote"].replace("15 in favour", "18 in favour")
    assert r.admit("cyprus", r.direct("cyprus") | {"vote": forged})[1]["vote"] == "not_exact_for_source"
    non_release = 0
    for arm in ("mali", "cyprus"):
        case, menu, state, world, rubric, evidence = r.load(arm)
        for bit, value in enumerate(state):
            if value < 0:
                continue
            partial = tuple(-1 if n == bit else v for n, v in enumerate(state))
            assert r.w.game.terminal(menu, partial)[0] == "UNRESOLVED"
            reduced = [item for item in evidence if item["id"] != "delivered"]
            reduced.append({"id": "delivered", "text": r.w.renderer.public_conditions(case, partial)})
            with patch.object(r, "load", return_value=(case, menu, partial, world, rubric, reduced)):
                _, reply, _ = r.compose(arm, r.direct(arm))
            assert reply["text"].splitlines()[0] == "Decision: UNRESOLVED"
            non_release += 1
    return {"arms": by_arm, "forge_and_cross_source_checks": 34,
            "single_reply_removals_requiring_deferral": non_release}


def verify():
    from jinja2.sandbox import ImmutableSandboxedEnvironment
    from tokenizers import Tokenizer

    assert r.pins() == e.read(r.RUN / "inputs.json")
    complete = e.read(r.RUN / "complete.json")
    assert set(complete) == {"launch.json", "inputs.json", "calls.jsonl", "tokens.jsonl"}
    assert all(digest(r.RUN / name) == contents for name, contents in complete.items())
    for archive in (r.OLD / "evidence", r.cy.RUN):
        pins = e.read(archive / "complete.json")
        assert all(digest(archive / name) == expected for name, expected in pins.items())
    launch = e.read(r.RUN / "launch.json")
    checkpoint = Path(launch["checkpoint"])
    assert launch["gpu_name"] == "NVIDIA RTX PRO 6000 Blackwell Server Edition" and launch["optimizer_updates"] == 0
    assert digest(checkpoint / "model.safetensors.index.json") == launch["checkpoint_index_sha256"]
    tpl = ImmutableSandboxedEnvironment(trim_blocks=True, lstrip_blocks=True).from_string(
        (checkpoint / "chat_template.jinja").read_text())
    tokenizer = Tokenizer.from_file(str(checkpoint / "tokenizer.json"))
    end = tokenizer.token_to_id("<|im_end|>")
    calls = rows("calls.jsonl")
    for arm, line, trace in zip(r.ARMS, calls, rows("tokens.jsonl"), strict=True):
        request = r.request(arm)
        assert arm == line["arm"] and request == line["request"]
        assert trace["response"] == line["reply"]
        inp = tokenizer.encode(tpl.render(messages=request["messages"], enable_thinking=False,
                                         add_generation_prompt=True, tools=None), add_special_tokens=False).ids
        reply, out = trace["response"], trace["output_ids"]
        assert inp == trace["input_ids"] and len(inp) == reply["input_tokens"]
        assert out and end not in out[:-1] and len(out) == reply["output_tokens"] <= request["max_output_tokens"]
        assert (out[-1] == end) == (reply["termination"] == "complete")
        assert tokenizer.decode(out, skip_special_tokens=True).strip() == reply["text"]
    return {"native_calls": len(calls), "optimizer_updates": launch["optimizer_updates"], "software": software()}


def deck():
    result = {}
    for arm, native in zip(r.ARMS, rows("calls.jsonl"), strict=True):
        assert arm == native["arm"]
        for method, candidates in (("direct", r.direct(arm)), ("native", r.parse(native["reply"]))):
            case, reply, fields = r.compose(arm, candidates)
            events = [{}, {}, reply]
            packet = e.final_packet(case, events)
            result[f"{arm}/{method}"] = case, events, packet, fields
    return result


def score():
    deck_rows = deck()
    marks = e.read(HERE / "marks.json")
    assert set(marks) == {packet["id"] for _, _, packet, _ in deck_rows.values()}
    return {key: {"admission": fields, "score": e.final_score(case, events, marks[packet["id"]])}
            for key, (case, events, packet, fields) in deck_rows.items()}


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode", choices=("verify", "packets", "score", "software"))
    mode = p.parse_args().mode
    e.emit({"verify": verify, "packets": lambda: {key: row[2] for key, row in deck().items()},
            "score": score, "software": software}[mode]())
