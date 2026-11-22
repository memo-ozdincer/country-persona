"""Build the ranked memo review packet and verify evidence annotations."""
import argparse
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path

import relay_memo_review as original
import relay_ranked_final as final

RUBRIC = final.ranked.relay.KIT / "ranked-final-rubric.json"


def packet(directory):
    with final.scenario():
        rows = original.verify(directory)
    result, key = {}, {}
    for row in rows:
        candidate = row["output"]
        prompt = row["expected"]
        id_ = sha256(("ranked-final-review/" + row["inference_id"]).encode()).hexdigest()[:10]
        key[row["id"]] = id_
        evidence = {name: json.dumps(value, ensure_ascii=False, sort_keys=True)
                    for name, value in prompt.items() if name != "instruction"}
        result[id_] = {"response": candidate, "evidence": evidence}
    assert len(key) == len(result)
    return {"rubric_sha256": sha256(RUBRIC.read_bytes()).hexdigest(), "items": dict(sorted(result.items()))}, key


def measure(deck, key, grades):
    rubric = json.loads(RUBRIC.read_text())
    assert grades["rubric_sha256"] == deck["rubric_sha256"]
    assert set(grades["reviews"]) == set(deck["items"])
    values = {}
    for id_, item in deck["items"].items():
        annotated = grades["reviews"][id_]
        assert set(annotated["units"]) == {u["id"] for u in rubric["units"]}
        for status, notes, spans, facts in (*annotated["units"].values(), annotated["guard"]):
            assert notes and (spans or status not in ("met", "failed"))
            assert all(span and span in item["response"] for span in spans)
            assert all(block in item["evidence"] and quote and quote in item["evidence"][block]
                       for block, quote in facts)
            assert facts or status not in ("met", "failed")
        levels = Counter(row[0] for row in annotated["units"].values())
        assert set(levels) <= {"met", "unmet", "uncertain"}
        heading = "Workshop status: " + json.loads(item["evidence"]["checked_status"])
        words = len(item["response"].split())
        guard = annotated["guard"][0]
        assert guard in ("clear", "failed", "uncertain")
        values[id_] = {
            "floor": rubric["points_per_unit"] * levels["met"],
            "ceiling": rubric["points_per_unit"] * (levels["met"] + levels["uncertain"]),
            "verified_heading": item["response"].splitlines()[0] == heading,
            "words": words, "under_cap": words <= rubric["words_max"],
            "guard": guard,
        }
    return {arm: values[id_] for arm, id_ in key.items()}


def run():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("directory", type=Path)
    cli.add_argument("--grades", type=Path)
    args = cli.parse_args()
    deck, key = packet(args.directory)
    if args.grades:
        print(json.dumps(measure(deck, key, json.loads(args.grades.read_text())), indent=2))
    else:
        for file, value in (("review-deck.json", deck), ("review-key.json", key)):
            (args.directory / file).write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    run()
