"""Verify the native trace and score source-grounded records from each public state."""
import argparse
from hashlib import sha256
from importlib.util import module_from_spec, spec_from_file_location
import json
from pathlib import Path

import witness as w

HERE = Path(__file__).resolve().parent
RELEASE = w.MALI.parents[2] / "benchmark-final"
spec = spec_from_file_location("benchmark_final_release_evaluate", RELEASE / "evaluate.py")
e = module_from_spec(spec)
spec.loader.exec_module(e)


def rows(name):
    return [json.loads(line) for line in (w.RUN / name).read_text().splitlines()]


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def verify():
    from jinja2.sandbox import ImmutableSandboxedEnvironment
    from tokenizers import Tokenizer

    complete = e.read(w.RUN / "complete.json")
    assert set(complete) == {"launch.json", "episodes.jsonl", "new-calls.jsonl", "tokens.jsonl", "inputs.json"}
    assert all(digest(w.RUN / name) == value for name, value in complete.items())
    assert all(digest(w.MALI / name) == value for name, value in e.read(w.RUN / "inputs.json").items())
    release = e.read(RELEASE / "release.json")
    assert release["version"] == "1.2"
    assert digest(Path(e.judge.__file__)) == release["sha256"]["judge_score.py"]
    assert all(digest(RELEASE / name) == value for name, value in release["sha256"].items())
    launch = e.read(w.RUN / "launch.json")
    old = e.read(w.MALI / "live" / "evidence" / "launch.json")
    for field in ("checkpoint", "checkpoint_index_sha256", "gpu_name", "decoding", "dtype", "attention"):
        assert launch[field] == old[field]
    assert launch["optimizer_updates"] == 0
    model = Path(launch["checkpoint"])
    assert digest(model / "model.safetensors.index.json") == launch["checkpoint_index_sha256"]
    tokenizer = Tokenizer.from_file(str(model / "tokenizer.json"))
    template = ImmutableSandboxedEnvironment(trim_blocks=True, lstrip_blocks=True).from_string(
        (model / "chat_template.jinja").read_text())
    end = tokenizer.token_to_id("<|im_end|>")
    calls = rows("new-calls.jsonl")
    native = iter(zip(calls, rows("tokens.jsonl"), strict=True))
    kinds = []

    def generate(kind, request):
        call, trace = next(native)
        assert kind == call["kind"] and request == call["request"] and call["reply"] == trace["response"]
        rendered = template.render(messages=request["messages"], add_generation_prompt=True,
                                   enable_thinking=False, tools=None)
        ids = tokenizer.encode(rendered, add_special_tokens=False).ids
        reply = call["reply"]
        assert ids == trace["input_ids"] and len(ids) == reply["input_tokens"]
        out = trace["output_ids"]
        assert out and len(out) == reply["output_tokens"] <= request["max_output_tokens"]
        assert end not in out[:-1] and (out[-1] == end) == (reply["termination"] == "complete")
        assert tokenizer.decode(out, skip_special_tokens=True).strip() == reply["text"]
        kinds.append(kind)
        return reply

    observed = rows("episodes.jsonl")
    assert json.loads(json.dumps(list(w.execute(generate)))) == observed
    assert next(native, None) is None
    assert [row["id"] for row in observed] == [f"{label}/{arm}" for label in w.roster() for arm in ("learned", "always")]
    return {"paths": len(observed), "physical_calls": {kind: kinds.count(kind) for kind in sorted(set(kinds))},
            "unique_older_sign_requests": len({w.key(step["request"]) for row in observed for step in row["steps"]
                                             if step.get("origin") == "archived"}),
            "optimizer_updates": launch["optimizer_updates"], "tokenizer_sha256": digest(model / "tokenizer.json")}


def records():
    model_case, menu, _, _ = w.load()
    rubric = e.read(w.MALI / "live" / "rubric.json")
    result = {}
    for row in rows("episodes.jsonl"):
        state = tuple(row["state"])
        task = json.loads(row["record"]["request"]["messages"][-1]["content"])["task"].removesuffix(" At most 225 words.")
        case = {"id": row["id"].split("/")[0] + "/" + ",".join(map(str, state)), "track": "workshop", "gold": [w.game.terminal(menu, row["world"])[0]],
                "word_cap": 225, "task": task, "rubric": rubric, "public": w.evidence(model_case, state), "owned": []}
        answers = {"native": row["record"]["reply"],
                   "compiled": {"text": w.renderer.render(model_case, menu, state), "termination": "complete"}}
        pairs = {}
        for label, answer in answers.items():
            calls = [{}, {}, answer]
            pairs[label] = calls, e.final_packet(case, calls)
        result[row["id"]] = row, case, pairs
    return result


def export():
    return {packet["id"]: packet for _, _, entries in records().values() for _, packet in entries.values()}


def score():
    marks = e.read(HERE / "marks.json")
    assert set(marks) == set(export())
    results = {}
    for path, (row, case, entries) in records().items():
        values = {}
        for name, (calls, packet) in entries.items():
            grades = e.final_score(case, calls, marks[packet["id"]])
            grades["public_decision_match"] = grades["mechanical"]["decision"] == row["certification"]
            values[name] = grades
        count = sum(step["send"] for step in row["steps"])
        results[path] = {"public_certification": row["certification"], "queries": len(row["steps"]),
                         "attempted_replies": count, "modeled_cost": round(.075 * len(row["steps"]) + .03 * count, 3),
                         "final_scores": values}
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("verify", "packets", "score"))
    fn = {"verify": verify, "packets": export, "score": score}[parser.parse_args().mode]
    e.emit(fn())
