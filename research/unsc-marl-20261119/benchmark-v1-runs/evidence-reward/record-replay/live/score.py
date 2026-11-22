"""Verify source-bound live replies and score their compiled outcomes."""
import argparse
from hashlib import sha256
import json
from pathlib import Path

import live

r = live.r
HERE = live.HERE
EVIDENCE = HERE / "evidence"


def rows(path):
    return [json.loads(line) for line in path.read_text().splitlines()]


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def inspect(evidence=EVIDENCE, pins=None, expected=None):
    from jinja2.sandbox import ImmutableSandboxedEnvironment
    from tokenizers import Tokenizer

    manifest = r.e.read(evidence / "complete.json")
    assert r.e.read(evidence / "followup-lock.json") == (live.pins() if pins is None else pins)
    assert set(manifest) == {"launch.json", "followup-lock.json", "records.jsonl", "tokens.jsonl"}
    assert all(digest(evidence / name) == sha for name, sha in manifest.items())
    launch = r.e.read(evidence / "launch.json")
    model = Path(launch["checkpoint"])
    assert digest(model / "model.safetensors.index.json") == launch["checkpoint_index_sha256"]
    assert launch["optimizer_updates"] == 0
    assert launch["gpu_name"] == "NVIDIA RTX PRO 6000 Blackwell Server Edition"
    t = Tokenizer.from_file(str(model / "tokenizer.json"))
    chat = model / "chat_template.jinja"
    template = ImmutableSandboxedEnvironment(trim_blocks=True, lstrip_blocks=True).from_string(chat.read_text())
    if expected is None:
        expected = [{"id": key, "request": req} for key, req in live.requests()]
    assert expected == r.e.read(evidence.parent / "requests.json") and len(expected) == 4
    actual = rows(evidence / "records.jsonl")
    for baseline, row, trace in zip(expected, actual, rows(evidence/"tokens.jsonl"), strict=True):
        assert baseline == {f: row[f] for f in ("id", "request")}
        request, reply = row["request"], row["response"]
        original = template.render(messages=request["messages"], add_generation_prompt=True,
                                   enable_thinking=False, tools=None)
        input_ids = t.encode(original, add_special_tokens=False).ids
        assert input_ids == trace["input_ids"] and len(input_ids) == reply["input_tokens"]
        assert trace["response"] == reply
        ids = trace["output_ids"]
        eos = t.token_to_id("<|im_end|>")
        assert len(ids) == reply["output_tokens"] <= request["max_output_tokens"]
        assert ids and eos not in ids[:-1]
        assert (ids[-1] == eos) == (reply["termination"] == "complete")
        assert t.decode(ids, skip_special_tokens=True).strip() == reply["text"]
    return {"verified_native_calls": len(actual), "optimizer_updates": launch["optimizer_updates"],
            "tokenizer_sha256": digest(model/"tokenizer.json"), "trainable_parameters_changed": 0}


def require_unique(pairs):
    obj = dict(pairs)
    if len(obj) != len(pairs):
        raise ValueError("Repeated JSON key")
    return obj


def parse(reply):
    if reply["termination"] != "complete":
        return None
    try:
        obj = json.loads(reply["text"], object_pairs_hook=require_unique)
    except ValueError:
        return None
    if not isinstance(obj, dict) or set(obj) != {"field", "value"} or any(
        not isinstance(v, str) for v in obj.values()
    ):
        return None
    return {obj["field"]: obj["value"]}


def score(records=None):
    grades = r.e.read(live.RECORD / "marks.json")
    archive = r.e.read(live.RECORD / "scores.json")["rates"]["0.8"]["arms"]
    no_followup = archive["no_followup"]
    actual = r.e.judge.by_id(rows(EVIDENCE / "records.jsonl") if records is None else records)
    expected_gain, attainable_gain, strict_gain = 0., 0., 0.
    results = {}
    for key, case, idx, signals, decision, archived_final_id, p_delivered in live.sources():
        row = actual[key]
        typed = parse(row["response"])
        packet = r.render.BASE.project(case)
        try:
            admitted = typed is not None and r.render.BASE.filter_local(
                packet["options"], {"requirement": typed}, case["membership"][idx])
        except ValueError:
            admitted = False
        mode = r.env.ROLES[idx]
        full = {mode: next(iter(typed.items()))} if admitted else {}
        final = r.render.final(packet, signals, full)
        earlier = r.render.final(packet, signals, {})
        assert final["decision"] == earlier["decision"] == decision

        def grade(record):
            calls = [{}, {}, {"text": record["text"], "termination": "complete"}]
            pid = r.e.final_packet(case, calls)["id"]
            return pid, r.e.final_score(case, calls, grades[pid])

        before_id, before = grade(earlier)
        final_id, after = grade(final)
        assert final_id == (archived_final_id if admitted else before_id)
        expected_gain += p_delivered * (after["released_70"] - before["released_70"])
        strict_gain += p_delivered * (after["strict"] - before["strict"])
        attainable_gain += (after["released_70"] - before["released_70"])
        results[key] = {"admitted": admitted, "observed_requirement": typed,
                        "role": case["roles"][idx], "before": before, "after": after,
                        "graded_text_id": final_id, "archived_full_text_id": archived_final_id,
                        "rendered_record": final["text"], "input_tokens": row["response"]["input_tokens"],
                        "output_tokens": row["response"]["output_tokens"],
                        "modeled_joint_delivery": p_delivered}
    assert set(actual) == set(results) and len(results) == 4
    signed_path = live.RUNS / "source-bound-chair/signed-coverage.json"
    signed = r.e.read(signed_path)["transitions"]
    reach = {}
    for name in ("native_frozen", "native_direct_credit", "native_reward", "feature_head", "exact_decision_reply"):
        eligible = [key for key in results if signed[key]["actors"][name]["admitted"]
                    and signed[key]["actors"][name]["signed_reply"] == "Y"]
        assert all(signed[key]["actors"][name]["terminal"] for key in eligible)
        points = sum(results[key]["modeled_joint_delivery"] * (
            results[key]["after"]["released_70"] - results[key]["before"]["released_70"]
        ) for key in eligible)
        reach[name] = {"eligible_contexts": eligible, "reachable_count": len(eligible),
                       "expected_released_point_gain_on_these_contexts": points}

    added_cost = archive["value"]["cost"] - no_followup["cost"]
    null_cost = no_followup["net"]
    return {"scope": "four live Qwen follow-ups on reconstructed first-stage histories",
            "observed_admitted_replies": sum(r["admitted"] for r in results.values()),
            "released_gain_if_all_first_and_second_replies_delivered": attainable_gain,
            "expected_gain_under_modeled_delivery": expected_gain,
            "expected_strict_pass_gain_under_modeled_delivery": strict_gain,
            "expected_proof": no_followup["exact"], "simulated_cost_difference": added_cost,
            "net_gain_on_normalized_released_points": expected_gain/70-added_cost,
            "net_value_total": null_cost + expected_gain/70-added_cost,
            "forced_opening_policy_reach": reach, "signed_archive_sha256": digest(signed_path),
            "results": results}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("verify", "score"))
    r.e.emit(inspect() if parser.parse_args().mode == "verify" else score())
