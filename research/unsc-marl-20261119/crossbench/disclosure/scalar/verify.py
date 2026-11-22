"""Replay private views, visible claims, validation and mechanical outcomes."""
import argparse
import json
from pathlib import Path

from transformers import AutoTokenizer

from run import digest
from scalar_protocol import HERE, ROOT, admit, family_inputs, request, script, summarize


def audit(path):
    launch = json.loads((path / "launch.json").read_text())
    complete = json.loads((path / "complete.json").read_text())
    for file in (HERE / "run.py", HERE / "scalar_protocol.py", HERE.parent / "protocol.py", *(ROOT / name for name in (
        "decision_ledger.py", "packets.py", "references.json", "workshops.json"))):
        assert digest(file) == launch["input_sha256"][file.name]
    transcript = path / "transcript.jsonl"
    assert digest(transcript) == complete["transcript_sha256"]
    assert launch["optimizer_updates"] == complete["optimizer_updates"] == 0
    rows = [json.loads(line) for line in transcript.read_text().splitlines()]
    by_id = {r["id"]: r for r in rows}
    assert len(rows) == len(by_id) == complete["records"] == 10
    roles, views, truth = family_inputs()
    tok = AutoTokenizer.from_pretrained(launch["model"], local_files_only=True)
    eos = tok.convert_tokens_to_ids("<|im_end|>")
    seen = set()
    receipts = {}

    def inspect(v, i, expected):
        row = by_id[expected["id"]]
        assert all(row[k] == value for k, value in expected.items())
        assert expected["id"] not in seen
        seen.add(expected["id"])
        prompt = tok.apply_chat_template(row["messages"], tokenize=False, add_generation_prompt=True,
                                         enable_thinking=False)
        assert tok.encode(prompt, add_special_tokens=False) == row["input_ids"]
        tokens = row["output_ids"]
        assert 0 < len(tokens) <= row["cap"] and eos not in tokens[:-1]
        assert (tokens[-1] == eos and row["stop"] == "eos") or (
            tokens[-1] != eos and len(tokens) == row["cap"] and row["stop"] == "cap")
        assert tok.decode(tokens, skip_special_tokens=True).strip() == row["output"]
        assert admit(row["output"], row["id"], roles[i], truth[v]["allowed_by_role"][i]) == row["judgment"]
        receipts[row["id"]] = {"model_output": row["output"], "judgment": row["judgment"],
                              "input_tokens": len(row["input_ids"]), "output_tokens": len(tokens)}
        return row

    def received(row):
        return row["judgment"]["admitted"]

    names = ("overlap", "impasse")
    open_1 = inspect("overlap", 0, request("open-1-shared", views["overlap"][0]))
    first = {v: [open_1, inspect(v, 1, request(f"open-2-{v}", views[v][1]))] for v in names}
    solo_1 = inspect("overlap", 0, request("solo-1-shared", views["overlap"][0], received(open_1), second=True))
    results, controls, costs = {}, {}, {}
    for v in names:
        solo_2 = inspect(v, 1, request(f"solo-2-{v}", views[v][1], received(first[v][1]), second=True))
        peer = [inspect(v, i, request(f"peer-{i+1}-{v}", views[v][i], received(first[v][i]),
                                      received(first[v][1-i]), second=True, peer_visible=True))
                for i in (0, 1)]
        records = {"opening": first[v], "solo": first[v] + [solo_1, solo_2], "peer": first[v] + peer}
        results[v] = {arm: summarize(roles, truth[v], ts) for arm, ts in records.items()}
        costs[v] = {arm: {
            "input_tokens": sum(len(r["input_ids"]) for r in ts),
            "generated_tokens": sum(len(r["output_ids"]) for r in ts),
            "cap_hits": sum(r["stop"] == "cap" for r in ts),
        } for arm, ts in records.items()}
        controls[v] = {arm: script(roles, truth[v], arm) for arm in
                       ("support_first", "exclusion_first", "public_A_probe")}
    assert seen == by_id.keys()
    assert results == json.loads((path / "metrics.json").read_text())
    assert controls == json.loads((path / "scripted.json").read_text())
    return {"records": len(rows), "transcript_sha256": digest(transcript),
            "optimizer_updates": 0, "outcomes": results, "costs": costs, "turns": receipts}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path)
    print(json.dumps(audit(parser.parse_args().run), indent=2, ensure_ascii=False))
