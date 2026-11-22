"""Replay exact prompt tokens, paired routing, choices and rewards from a baseline run."""
import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path

from transformers import AutoTokenizer

from environment import ABSENT, HOLD, outcome, text_view
from qwen_baseline import cases


def read(path):
    return json.loads(path.read_text())


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path)
    parser.add_argument("receipt", type=Path)
    args = parser.parse_args()
    launch = read(args.run / "launch.json")
    complete = read(args.run / "complete.json")
    assert complete["optimizer_updates"] == launch["optimizer_updates"] == 0
    for name, expected in complete["records_sha256"].items():
        assert digest(args.run / name) == expected
    for name, expected in launch["input_sha256"].items():
        assert digest(Path(__file__).with_name(name)) == expected
    tokenizer = AutoTokenizer.from_pretrained(launch["model_path"], local_files_only=True)
    rows = [json.loads(line) for line in (args.run / "actions.jsonl").read_text().splitlines()]
    actions = {(r["family"], r["arm"], r["profile"], r["option_order_variant"], r["role"]): r for r in rows}
    assert len(actions) == len(rows) == complete["action_records"]
    evaluated = set()
    scores = {}
    for family, arms in read(args.run / "episodes.json").items():
        worlds = cases(family)

        def check(arm, phase, case_id, role, own=ABSENT, inbox=ABSENT):
            key = (family, arm, case_id // 2, case_id % 2, role)
            evaluated.add(key)
            row = actions[key]
            expected_prompt = text_view(worlds[case_id], role, phase, peer=inbox, own=own)
            assert (row["phase"], row["prompt"]) == (phase, expected_prompt)
            rendered = tokenizer.apply_chat_template(
                [{"role": "user", "content": expected_prompt}], tokenize=False, add_generation_prompt=True,
                enable_thinking=False,
            )
            assert tokenizer.encode(rendered, add_special_tokens=False) == row["input_ids"]
            probs = row["conditional_probs"]
            assert list(probs) == list("H" + "ABCD"[:len(worlds[case_id]["options"])])
            assert all(0 <= prob <= 1 for prob in probs.values())
            assert math.isclose(sum(probs.values()), 1, abs_tol=1e-5) and 0 < row["legal_mass"] <= 1
            best = max(probs, key=probs.get)
            assert (row["action_letter"], row["action"]) == (best, list(probs).index(best) + HOLD)
            return row["action"]

        signals = [[check("shared", "proposal", i, role) for role in range(2)] for i in range(len(worlds))]
        scores[family] = {}
        for arm, episodes in arms.items():
            assert len(episodes) == len(worlds)
            counts = Counter()
            for i, (case, reported) in enumerate(zip(worlds, episodes)):
                if arm == "silent":
                    inbox = [ABSENT, ABSENT]
                else:
                    donor = (i + 2) % len(worlds) if arm == "shuffled" else i
                    inbox = signals[donor][::-1]
                votes = [check(arm, "ballot", i, role, signals[i][role], inbox[role]) for role in range(2)]
                grade = outcome(case, signals[i], votes)
                assert reported == dict(case=case, signals=signals[i], received=inbox, ballots=votes, **grade)
                group = "agreement" if grade["feasible"] else "deadlock"
                counts[group] += 1
                counts[f"strict_{group}"] += grade["strict"]
                for key in ("false_hold", "unsupported_signal", "unsupported_ballot"):
                    counts[key] += grade[key]
            agreement = counts["strict_agreement"] / counts["agreement"]
            deadlock = counts["strict_deadlock"] / counts["deadlock"]
            scores[family][arm] = {
                **counts,
                "balanced_success": (agreement + deadlock) / 2,
                "placement_sensitive_profiles": sum(
                    a["strict"] != b["strict"] for a, b in zip(episodes[::2], episodes[1::2])
                ),
            }
        for control in ("silent", "shuffled"):
            scores[family][f"peer_vs_{control}"] = dict(Counter(
                f"{'met' if a['strict'] else 'failed'}_vs_{'met' if b['strict'] else 'failed'}"
                for a, b in zip(arms["peer"], arms[control])
            ))
    assert evaluated == set(actions)
    with args.receipt.open("x") as file:
        json.dump({"verified_action_records": len(rows), "scores": scores, "min_legal_mass": min(
            r["legal_mass"] for r in rows
        ), "max_legal_mass": max(r["legal_mass"] for r in rows)}, file, indent=2)
        file.write("\n")


if __name__ == "__main__":
    main()
