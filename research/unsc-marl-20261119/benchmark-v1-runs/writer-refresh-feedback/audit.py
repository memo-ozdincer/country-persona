"""Replay release and learning from the saved chronological episodes."""
from collections import Counter
from hashlib import sha256
from pathlib import Path
import json

HERE = Path(__file__).resolve().parent


def audit(result, plan):
    checks = Counter()
    archive_paths = {
        "compact": "../delisting-witness-render/compact-results.json",
        "topic": "../delisting-focused-writer/results.json",
    }

    def fingerprint(pair, prefix, answer):
        payload = json.dumps([pair, prefix, answer], ensure_ascii=False, sort_keys=True)
        return sha256(payload.encode()).hexdigest()

    for writer, path in archive_paths.items():
        archive = json.loads((HERE / path).read_text())["compiled"]
        for candidate in result["candidates"][writer]:
            if candidate is None:
                continue
            pair = candidate["pair"]
            record = archive[pair]
            prefix, answer = record["prefix"], record["ungated_record"]
            assert fingerprint(pair, prefix, answer) == candidate["id"]
            assert fingerprint(pair, prefix + " ", answer) != candidate["id"]
            assert fingerprint(pair, prefix, answer + " ") != candidate["id"]
            assert candidate["score"] == record["scores"]["ungated"]
            checks["exact_candidate_ids"] += 1
    for arms in result["variants"].values():
        for phases in arms.values():
            cache = {}
            for phase, mix in plan["phases"]:
                rows = phases[phase]
                estimates = dict(enumerate(result["base"]))
                count, total = Counter(), Counter()
                shadows = 0
                for i, row in enumerate(rows["trace"], 1):
                    assert row["first_received"] == (row["send"] and row["delivery_draws"][0] < row["q"][0])
                    assert row["reply_received"] == (row["delivery_draws"][1] < row["q"][1])
                    assert row["send_fee"] == (row["price"] if row["send"] else 0)
                    first, back = row["first_received"], row["reply_received"]
                    view, reply = row["view"], row["reply"]
                    if first and back:
                        key = 6 + 2 * view + reply
                    elif first:
                        key = 1 + view
                    else:
                        key = 4 + reply if back else 0
                    assert row["receipt"] == key
                    assert mix[("compact", "topic").index(row["writer"])] > 0
                    candidate = result["candidates"][row["writer"]][key-6] if key >= 6 else None
                    original = result["base"][key]
                    ident = candidate["id"] if candidate else None
                    assert row["candidate_id"] == ident
                    assert row["released"] == cache.get(ident, original)
                    assert row["reviewed_now"] == (ident is not None and ident not in cache)
                    if row["reviewed_now"]:
                        cache[ident] = max(original, candidate["score"])
                        shadows += 1
                    assert row["score_signal"] == cache.get(ident, original)
                    count[key] += 1
                    total[key] += row["score_signal"]
                    estimates[key] = total[key] / count[key]
                    if i in plan["checkpoints"]:
                        snap = rows["checkpoints"][str(i)]
                        assert snap["estimates"] == list(estimates.values())
                        assert snap["counts"] == [count[k] for k in estimates]
                        assert snap["review_count"] == shadows
                    checks["episodes"] += 1
                    checks["shadow_reviews"] += int(row["reviewed_now"])
                    checks["released_comparisons"] += int(row["released"] == 70)
    for arm in result["variants"]["continuous"]:
        for phase, rows in result["variants"]["continuous"][arm].items():
            limit = plan["exploration_windows"]["bounded"]
            bounded = result["variants"]["bounded"][arm][phase]["trace"]
            assert [(r["q"], r["view"], r["price"], r["delivery_draws"], r["writer"]) for r in bounded] == [
                (r["q"], r["view"], r["price"], r["delivery_draws"], r["writer"]) for r in rows["trace"]
            ]
            if phase == "compact":
                assert bounded[:limit] == rows["trace"][:limit]
    return dict(checks)


if __name__ == "__main__":
    data = [json.loads((HERE / name).read_text()) for name in ("results.json", "plan.json")]
    print(json.dumps(audit(*data), indent=2))
