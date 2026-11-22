"""Verify and score the eight live UNIFIL writer outputs."""
import argparse
from hashlib import sha256
import json
from pathlib import Path

import collect_writer as collection

HERE = Path(__file__).resolve().parent
E, witness = collection.E, collection.witness
RUN = HERE / "evidence"


def rows(name):
    return [json.loads(line) for line in (RUN / name).read_text().splitlines()]


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def verify():
    from jinja2.sandbox import ImmutableSandboxedEnvironment
    from tokenizers import Tokenizer

    manifest = E.read(RUN/"complete.json")
    assert set(manifest) == {"launch.json","tokens.jsonl","records.jsonl","writer-lock.json"}
    assert all(digest(RUN / name) == v for name,v in manifest.items())
    assert E.read(RUN/"writer-lock.json") == collection.pins()
    launch = E.read(RUN/"launch.json")
    model = Path(launch["checkpoint"])
    assert digest(model/"model.safetensors.index.json") == launch["checkpoint_index_sha256"]
    assert launch["optimizer_updates"] == 0
    assert launch["gpu_name"] == "NVIDIA RTX PRO 6000 Blackwell Server Edition"
    t = Tokenizer.from_file(str(model/"tokenizer.json"))
    env = ImmutableSandboxedEnvironment(trim_blocks=True,lstrip_blocks=True)
    template = env.from_string((model/"chat_template.jinja").read_text())
    expected = collection.deck()
    actual, traces = rows("records.jsonl"), rows("tokens.jsonl")
    eos = t.token_to_id("<|im_end|>")
    for key, row, trace in zip(expected, actual, traces, strict=True):
        assert key == {k:row[k] for k in ("id","request")}
        request, response = row["request"], row["response"]
        chat = template.render(messages=request["messages"],add_generation_prompt=True,
                               enable_thinking=False,tools=None)
        ids = t.encode(chat,add_special_tokens=False).ids
        assert ids == trace["input_ids"] and len(ids) == response["input_tokens"]
        assert response == trace["response"]
        new = trace["output_ids"]
        assert new and len(new) == response["output_tokens"] <= request["max_output_tokens"]
        assert eos not in new[:-1] and (new[-1] == eos) == (response["termination"] == "complete")
        assert t.decode(new, skip_special_tokens=True).strip() == response["text"]
    return {"live_finals_verified": len(actual), "training_steps": 0,
            "tokenizer_sha256": digest(model/"tokenizer.json")}


def packets():
    _, cases, _ = witness.prepare()
    deck, mapping = {}, {}
    for row in rows("records.jsonl"):
        condition, phase = row["id"].split("/")
        case = cases[condition][phase]
        calls = [{},{},row["response"]]
        packet = E.final_packet(case, calls)
        if packet["id"] in deck:
            assert deck[packet["id"]] == packet
        deck[packet["id"]] = packet
        mapping[row["id"]] = (case,calls,packet)
    assert len(mapping) == 8
    return [deck[key] for key in sorted(deck)], mapping


def score():
    deck, mapping = packets()
    scores = E.read(HERE/"marks.json")
    assert set(scores) == {p["id"] for p in deck}
    scores_ref = E.read(witness.HERE/"scored.json")["results"]
    records = {}
    for key, (case,calls,packet) in mapping.items():
        condition, phase = key.split("/")
        result = E.final_score(case,calls,scores[packet["id"]])
        records.setdefault(condition, {})[phase] = {
            "model": result, "reference": scores_ref[condition]["scores"][phase],
            "id": packet["id"], "stop": calls[-1]["termination"],
            "input_tokens": calls[-1]["input_tokens"], "output_tokens": calls[-1]["output_tokens"],
        }
    effects = {}
    for cond, phases in records.items():
        effects[cond] = {kind: phases["after"][kind]["released_70"] - phases["before"][kind]["released_70"]
                         for kind in ("model","reference")}
    return {"annotation": "same-assistant source and transcript review",
            "records": records, "additional_released_points": effects}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode",choices=("verify","deck","score"))
    mode = parser.parse_args().mode
    E.emit(verify() if mode=="verify" else packets()[0] if mode=="deck" else score())
