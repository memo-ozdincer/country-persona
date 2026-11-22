"""Score note provenance and final criteria for Resolution 2719."""
import argparse
import json
from pathlib import Path

import facilitator_resolution_2719 as study

IDEAS = {"A1", "A2", "A3", "U1", "U2", "F1", "F2", "F3"}


def ceilings(criteria):
    return [42 + sum(c["points"] for c in criteria if c["mask"] & mask == c["mask"]) for mask in range(8)]


def score(rows, marks):
    criteria = {c["id"]: c for c in study.packet()["criteria"]}
    blinded = study.blind(rows)
    assert blinded.keys() == marks.keys()
    report = {}
    for arm, (alias, texts) in zip(study.ARMS, blinded.items(), strict=True):
        review = marks[alias]
        assert review["criteria"].keys() == criteria.keys()
        supplement = texts["supplement"]
        points = 42
        for key, (status, spans) in review["criteria"].items():
            assert status in {"met", "unmet", "uncertain"}
            assert all(span and span in supplement for span in spans)
            if status == "met":
                assert spans
                points += criteria[key]["points"]
        assert all(span and span in supplement for span in review["material_errors"])
        assert len(review["notes"]) == len(texts["notes"])
        seen, unique = set(), []
        for text, idea_map in zip(texts["notes"], review["notes"], strict=True):
            assert idea_map.keys() <= IDEAS and all(span and span in text for span in idea_map.values())
            unique.append(sorted(idea_map.keys() - seen))
            seen.update(idea_map)
        assert len(review["note_errors"]) == len(texts["notes"])
        for text, errors in zip(texts["notes"], review["note_errors"], strict=True):
            assert all(error and error in text for error in errors)
        for link in review["uptake"]:
            assert 0 <= link["from"] < link["to"] < len(texts["notes"])
            assert link["earlier"] and link["earlier"] in texts["notes"][link["from"]]
            assert link["later"] and link["later"] in texts["notes"][link["to"]]
            assert link["final"] in supplement and link["relation"]
        tail = rows[f"{arm}/3"]
        words = len(supplement.split())
        released = bool(tail["ended"] and words <= 154 and not review["material_errors"])
        reports = [rows[f"{arm}/{i}"] for i in range(4)]
        report[arm] = {"review": review, "points": points, "released": released,
                       "release_points": points if released else 0,
                       "record": " ".join(study.packet()["public"]) + "\n\n" + supplement,
                       "supplement_words": words,
                       "turns": len(reports) - 1, "total_calls": len(reports), "new_ideas": unique,
                       "new_private_ideas": [[idea for idea in label if idea != "A3"] for label in unique],
                       "note_words": [len(note.split()) for note in texts["notes"]],
                       "interaction_count": len(review["uptake"]),
                       "interactions_in_final": sum(bool(x["final"]) for x in review["uptake"]),
                       "input_tokens": sum(len(r["input_ids"]) for r in reports),
                       "output_tokens": sum(len(r["output_ids"]) for r in reports)}
    ceiling = ceilings(criteria.values())
    assert ceiling == [42, 48, 47, 53, 49, 59, 54, 70]
    return {"ceilings": ceiling, "results": report}


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("directory", type=Path)
    d = p.parse_args().directory
    rows = study.verify(d)
    print(json.dumps(score(rows, json.loads((d / "review.json").read_text())), ensure_ascii=False, indent=2))
