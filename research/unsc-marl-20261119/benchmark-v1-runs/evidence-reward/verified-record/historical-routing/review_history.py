"""Replay the role prompts and project final-record scores through frozen routes."""
import argparse
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path

import historical as h

HERE = Path(__file__).resolve().parent
e = h.e


def rows(path):
    return [json.loads(line) for line in path.read_text().splitlines()]


def sha(path):
    return sha256(path.read_bytes()).hexdigest()


def verify():
    from jinja2.sandbox import ImmutableSandboxedEnvironment
    from tokenizers import Tokenizer

    end_to_end = e.read(h.RUN / "complete.json")
    assert set(end_to_end) == {"launch.json", "calls.jsonl", "tokens.jsonl", "inputs.json"}
    assert all(sha(h.RUN / key) == digest for key, digest in end_to_end.items())
    assert h.pins() == e.read(h.RUN / "inputs.json")
    release = e.read(e.HERE / "release.json")
    assert all(sha(e.HERE / name) == expected for name, expected in release["sha256"].items())
    assert h.requests() == e.read(HERE / "requests.json")
    launch = e.read(h.RUN / "launch.json")
    assert launch["optimizer_updates"] == 0
    assert launch["gpu_name"] == "NVIDIA RTX PRO 6000 Blackwell Server Edition"
    model = Path(launch["checkpoint"])
    assert sha(model / "model.safetensors.index.json") == launch["checkpoint_index_sha256"]
    tpl = ImmutableSandboxedEnvironment(trim_blocks=True, lstrip_blocks=True).from_string(
        (model / "chat_template.jinja").read_text())
    tok = Tokenizer.from_file(str(model / "tokenizer.json"))
    eos = tok.token_to_id("<|im_end|>")
    receipts = rows(h.RUN / "calls.jsonl")
    tests = 0
    for (desk, request), call, token in zip(h.requests().items(), receipts, rows(h.RUN / "tokens.jsonl"), strict=True):
        assert desk == call["desk"] and call["request"] == request
        assert call["reply"] == token["response"]
        text = tpl.render(messages=request["messages"], enable_thinking=False, add_generation_prompt=True, tools=None)
        ids, out = token["input_ids"], token["output_ids"]
        assert ids == tok.encode(text, add_special_tokens=False).ids
        reply = call["reply"]
        assert len(ids) == reply["input_tokens"] and len(out) == reply["output_tokens"] <= request["max_output_tokens"]
        assert out and eos not in out[:-1] and (out[-1] == eos) == (reply["termination"] == "complete")
        assert tok.decode(out, skip_special_tokens=True).strip() == reply["text"]
        payload = json.loads(request["messages"][-1]["content"])
        assert len(payload["evidence"]) == 2 and payload["desk"] == desk
        tests += len(payload["evidence"])
    return {"native_calls": len(receipts), "local_blocks_in_prompts": tests,
            "admitted_counts_by_desk": [len(group) for group in h.admitted()], "optimizer_updates": 0}


def normalize_reply(desk, proposed):
    # This narrow adapter handles an echoed request envelope. It cannot license
    # a key, source or text that the existing exact matcher would reject.
    if set(proposed) == {"desk", "evidence"}:
        expected = proposed["desk"] == desk and isinstance(proposed["evidence"], dict)
        return proposed["evidence"] if expected else {}
    return proposed


def canonical_admission():
    _, packet = h.case_data()
    calls = rows(h.RUN / "calls.jsonl")
    result = []
    for call, card in zip(calls, packet["cards"], strict=True):
        assert call["desk"] == card["desk"]
        proposed = normalize_reply(card["desk"], h.r.parse(call["reply"]))
        result.append([atom["id"] for atom in card["atoms"] if proposed.get(atom["id"]) == atom["text"]])
    assert normalize_reply("Peru", {"desk": "Serbia", "evidence": {}}) == {}
    assert normalize_reply("Peru", {"desk": "Peru", "evidence": "not a map"}) == {}
    return result


def compressed(admissions):
    templates = e.read(HERE / "compact.json")
    records = {}
    for mask in range(8):
        available = []
        excerpts = []
        for index, (fields, template) in enumerate(zip(admissions, templates, strict=True)):
            if not mask & (1 << index) or not fields:
                continue
            available.extend(fields)
            excerpts.append(template["both"] if len(fields) == 2 else template[fields[0]])
        suffix = " ".join(excerpts)
        assert len(suffix.split()) <= 70
        records[mask] = {"available": available, "kept": available,
                         "historical_record": h.BASE + ("\n\n" + suffix if suffix else "")}
    return records


def packets():
    case, packet = h.case_data()
    output = {}
    original = canonical_admission()
    reversed_order = [list(reversed(x)) for x in original]
    for endpoint in ("strict", "legacy", "v1.2", "compact"):
        if endpoint == "compact":
            records = compressed(original)
            reversed_records = compressed(reversed_order)
            assert all(row["historical_record"] == reversed_records[mask]["historical_record"]
                       for mask, row in records.items())
        elif endpoint == "strict":
            records = h.records("v1.2", h.admitted())
        else:
            records = h.records(endpoint, original)
            assert h.records(endpoint, reversed_order) == records
        for mask, record in records.items():
            keyed = case | {"id": f"historical-2422/{mask}"}
            marks = e.final_packet(keyed, [{}, {}, {"text": record["historical_record"]}])
            output[f"{endpoint}/{mask}"] = record | {"packet": marks}
    return output


def propagate(deck):
    case, packet = h.case_data()
    forecasts = e.read(h.ARCHIVE / "forecast.json")["budgets"]["70"]
    free = e.read(h.ARCHIVE / "writer-results.json")["records"]
    marks = e.read(HERE / "marks.json")
    assert set(marks) == {row["packet"]["id"] for row in deck.values()}
    weights = {key["id"]: key["weight"] for key in case["rubric"]}
    scored = {}
    for key, record in deck.items():
        method, mask = key.split("/")
        row = record["packet"]
        response = {"text": row["answer"], "termination": "complete"}
        reference = case | {"id": f"historical-2422/{mask}"}
        score = e.final_score(reference, [{}, {}, response], marks[row["id"]])
        core = sum(weights[k] for k in record["kept"])
        contrast = set(packet["joint"]["needs"]) <= set(record["kept"])
        supplement = core + weights["contrast"] * contrast
        guarded = score["release"]
        scored[key] = {"released_70": score["released_70"], "supplement_28": supplement if guarded else 0,
                       "words": score["words"], "guard": score["guard"], "kept": record["kept"]}
        if method == "legacy":
            score_ceiling = forecasts["excerpt_scores"][int(mask)] - packet["base_points"]
            assert supplement <= score_ceiling
    matrices = {
        "strict_parser_v1.2": [scored[f"strict/{i}"]["released_70"] for i in range(8)],
        "native_compiled_legacy": [scored[f"legacy/{i}"]["supplement_28"] for i in range(8)],
        "native_compiled_v1.2": [scored[f"v1.2/{i}"]["released_70"] for i in range(8)],
        "compact_supplement": [scored[f"compact/{i}"]["supplement_28"] for i in range(8)],
        "compact_v1.2": [scored[f"compact/{i}"]["released_70"] for i in range(8)],
        "free_forward_supplement": [free["forward"][str(i)]["released"] for i in range(8)],
        "free_reversed_supplement": [free["reverse"][str(i)]["released"] for i in range(8)],
    }
    expected = {}
    for law, roster in forecasts["laws"].items():
        values = {}
        for endpoint, scores in matrices.items():
            rows = {}
            for name, policy in roster["arms"].items():
                mass = policy["receipt_mass"]
                assert abs(sum(mass) - 1.) < 1e-10
                points = sum(p * v for p, v in zip(mass, scores, strict=True))
                rows[name] = {"expected_released": points, "cost": policy["cost"], "net": points - policy["cost"]}
            silence = rows["same_responder_silence"]["net"]
            for value in rows.values():
                value["net_over_same_responder_silence"] = value["net"] - silence
            values[endpoint] = rows
        expected[law] = values
    return {"strict_native_admission": h.admitted(), "normalized_native_admission": canonical_admission(),
            "records": scored, "expected": expected,
            "final_benchmark_rubric": Counter(weights),
            "score_inputs_sha256": {p.name: sha(p) for p in (Path(__file__), HERE / "compact.json",
                HERE / "compression-protocol.md", HERE / "normalization-protocol.md", HERE / "marks.json")}}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("verify", "packets", "score"))
    mode = parser.parse_args().mode
    if mode == "verify":
        e.emit(verify())
    else:
        deck = packets()
        e.emit(deck if mode == "packets" else propagate(deck))
