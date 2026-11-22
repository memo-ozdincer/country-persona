"""Check token replay and pairwise reward preferences for the DRC judge."""
import argparse
import json
from pathlib import Path

import experts_judge as judge


def run(directory):
    from transformers import AutoTokenizer

    launch = json.loads((directory / "launch.json").read_text())
    tokenizer = AutoTokenizer.from_pretrained(launch["model_path"], local_files_only=True)
    actions = [json.loads(line) for line in (directory / "actions.jsonl").read_text().splitlines()]
    for action in actions:
        rendered = tokenizer.apply_chat_template(action["messages"], tokenize=False,
                                                 add_generation_prompt=True, enable_thinking=False)
        encoding = tokenizer.encode(rendered, add_special_tokens=False)
        assert action["input_ids"] == encoding
        for label, token in zip("ABC", action["label_ids"], strict=True):
            assert tokenizer.encode(rendered + label, add_special_tokens=False) == encoding + [token]

    report = judge.report(directory)
    rows = report["rows"]
    matrix = {}
    categories = {status: status for status in judge.STATUS}
    categories["deferred"] = None
    for group in report["groups"]:
        selection = [r for r in rows if r["group"] == group]
        matrix[group] = {truth: {verdict: sum(r["reference"] == truth and r["verdict"] == value
                                            for r in selection)
                                 for verdict, value in categories.items()}
                         for truth in judge.STATUS}

    pairs = {}
    authored = {(r["field"], r["candidate_id"]): r for r in rows if r["group"] == "authored"}
    for case in ("omission", "wrong_value"):
        outcomes = []
        for field in judge.FIELDS:
            preferred = authored[field, "complete"]
            alternative = authored[field, case]
            outcomes.append({"field": field,
                             "complete_verdict": preferred["verdict"], "edited_verdict": alternative["verdict"],
                             "strict_preference": preferred["verdict"] == "stated"
                                                  and alternative["verdict"] != "stated"})
        pairs[case] = {"complete_strictly_rewarded_more": sum(r["strict_preference"] for r in outcomes),
                       "edited_still_rewarded": sum(r["edited_verdict"] == "stated" for r in outcomes),
                       "n": len(outcomes), "records": outcomes}
    return {"exact_token_replay_count": len(actions), "confusion_counts": matrix,
            "pairs_for_one_point_of_stable_credit": pairs}


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("directory", type=Path)
    print(json.dumps(run(cli.parse_args().directory), indent=2))
