"""Prepare blind packets and score assistant marks with the release validator."""
import argparse
from hashlib import sha256
import json

from study import CASE, DESKS, HERE, OUT, RELEASE, load_module, read

judge = load_module("frozen_final_judge", RELEASE / "judge_score.py")


def packets():
    answer_rows = read(OUT / "briefs.json")
    evidence = [{"id": row["id"], "text": row["text"]} for row in CASE["evidence"]]
    return {
        key: judge.request({
            "id": sha256(key.encode()).hexdigest()[:20],
            "mode": "FINAL",
            "task": CASE["task"],
            "evidence": evidence,
            "rubric": CASE["rubric"],
            "answer": row["final"]["text"],
        })
        for key, row in answer_rows.items()
    }


def score():
    inputs = packets()
    annotations = read(HERE / "marks.json")
    replies = read(OUT / "briefs.json")
    assert set(annotations) == {packet["id"] for packet in inputs.values()}
    results = {}
    for key, packet in inputs.items():
        marks = annotations[packet["id"]]
        result = judge.score(packet, marks)
        reply = replies[key]
        words = len(packet["answer"].split())
        blockers = []
        if result["guard"] != "clear":
            blockers.append("guard_" + result["guard"])
        if reply["final"]["termination"] != "complete":
            blockers.append("incomplete")
        if not 0 < words <= CASE["word_cap"]:
            blockers.append("word_count")
        results[key] = {
            "id": packet["id"],
            "final": result["final"], "guard": result["guard"],
            "released": result["final"]["lower"] if not blockers else 0,
            "strict": result["strict"] and not blockers, "words": words,
            "blockers": blockers, "input_tokens": reply["input_tokens"],
            "output_tokens": reply["output_tokens"],
        }
    contrasts = {}
    for order in DESKS:
        peer = results[f"peer/{order}/final"]
        contrasts[order] = {
            arm: {metric: peer[metric] - results[f"{arm}/{order}/final"][metric]
                  for metric in ("released", "input_tokens", "output_tokens")}
            for arm in ("independent", "solo")
        }
    return {"results": results, "peer_minus_control": contrasts}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--blind", action="store_true")
    args = parser.parse_args()
    results = sorted(packets().values(), key=lambda packet: packet["id"]) if args.blind else score()
    print(json.dumps(results, ensure_ascii=False, indent=2))
