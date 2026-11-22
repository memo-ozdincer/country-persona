"""Replay the frozen pilot's token records, dependencies and budget without a model."""
import argparse
import json
from pathlib import Path

from transformers import AutoTokenizer

from country_persona.inference_probe import stop_trace
from country_persona.io import sha256, write_json

HERE = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path)
    parser.add_argument("receipt", type=Path)
    args = parser.parse_args()
    launch = json.loads((args.run / "launch.json").read_text())
    complete = json.loads((args.run / "complete.json").read_text())
    assert all(sha256(HERE / name) == value for name, value in launch["input_sha256"].items())
    transcript = args.run / "transcript.jsonl"
    assert sha256(transcript) == complete["transcript_sha256"]
    rows = [json.loads(line) for line in transcript.read_text().splitlines()]
    assert len(rows) == complete["completed_calls"] == 9
    records = {row["id"]: row for row in rows}
    assert list(records) == ["opening-india", "opening-pacific", "solo-india", "solo-pacific",
                             "final-solo", "peer-india", "peer-pacific", "final-peer", "final-analyst"]

    tokenizer = AutoTokenizer.from_pretrained(launch["model_path"], local_files_only=True)
    for row in rows:
        rendered = tokenizer.apply_chat_template(row["messages"], tokenize=False, add_generation_prompt=True,
                                                 enable_thinking=False)
        assert tokenizer.encode(rendered, add_special_tokens=False) == row["input_ids"]
        assert tokenizer.decode(row["generated_ids"], skip_special_tokens=True).strip() == row["output"]
        assert len(row["input_ids"]) == row["prompt_tokens"]
        assert len(row["generated_ids"]) == row["generated_tokens"]
        config = row["generation_config"]
        assert row["prompt_tokens"] + config["max_new_tokens"] <= 4096 and config["do_sample"] is False
        eos = config["eos_token_id"]
        for key, value in stop_trace(row["generated_ids"], eos, eos, config["max_new_tokens"]).items():
            assert row[key] == value
        if row["id"].startswith("opening-") or row["id"] == "final-analyst":
            assert row["dependencies"] == []

    def text(case):
        return records[case]["messages"][-1]["content"]

    def output(case):
        return records[case]["output"]

    def group(arm):
        return ["opening-india", "opening-pacific", f"{arm}-india", f"{arm}-pacific", f"final-{arm}"]

    for role, other in (("india", "pacific"), ("pacific", "india")):
        own_opening, peer_opening = f"opening-{role}", f"opening-{other}"
        solo, peer = f"solo-{role}", f"peer-{role}"
        assert records[solo]["dependencies"] == [own_opening]
        assert records[peer]["dependencies"] == [own_opening, peer_opening]
        common = f"Your opening:\n{output(own_opening)}\n\n"
        assert text(solo).split(common) == [
            text(peer).split(common)[0],
            "You are revising independently. No peer opening has been supplied.\n\n"
            + text(peer).split(f'\n{output(peer_opening)}\n\n', 1)[1],
        ]

    for arm in ("solo", "peer"):
        final = f"final-{arm}"
        assert records[final]["dependencies"] == [f"{arm}-india", f"{arm}-pacific"]
        for case in records[final]["dependencies"]:
            assert f"\n{output(case)}\n\n" in text(final)
        prefix, remainder = text(final).split("\n\nSubmissions:\n", 1)
        assert prefix + "\n\n" + remainder.rsplit("\n\n", 1)[1] == text("final-analyst")

    arms = {"solo": group("solo"), "peer": group("peer"), "analyst": ["final-analyst"]}
    metrics = {
        arm: {
            "input_tokens": sum(records[case]["prompt_tokens"] for case in cases),
            "output_tokens": sum(records[case]["generated_tokens"] for case in cases),
            "output_ceiling": sum(records[case]["generation_config"]["max_new_tokens"] for case in cases),
            "cap_hits": [case for case in cases if records[case]["hit_output_cap"]],
            "final_words": len(output(f"final-{arm}").split()),
        }
        for arm, cases in arms.items()
    }
    assert len({stats["output_ceiling"] for stats in metrics.values()}) == 1
    write_json(args.receipt, {
        "transcript_sha256": complete["transcript_sha256"], "verified_calls": len(rows), "arm_metrics": metrics,
        "scope": "Frozen file hashes, actual prompt and output tokens, stop reasons, dependency text and budgets.",
    })


if __name__ == "__main__":
    main()
