"""Reproduce selected frozen actions and audit how their evidence survives."""
import argparse
from hashlib import sha256
import json
import sys

from live_transfer import EVIDENCE, FAMILY, HERE, KIT, PACKET, PROTOCOL, load, pins, plan
sys.path.insert(0, str(KIT / "bosnia2604-routing/protected-record"))
from score_protected import read_rows, verify_generation


def masked(key):
    return sha256(("2719-live/" + key).encode()).hexdigest()[:10]


def score_batch(directory, family, requests, pins, paths, annotations, mask):
    rows = read_rows(directory)
    verify_generation(directory, rows, requests, family, pins)
    assert len(rows) == 6
    marks = load(annotations / "marks.json")
    assert marks.keys() == {mask(k) for k in rows}
    config = load(PROTOCOL)
    rubric = {r["id"]: r["points"] for r in load(PACKET)["criteria"]}
    checks = {}
    for key, row in rows.items():
        text = row["output"]
        m = marks[mask(key)]
        assert m["spans"].keys() == rubric.keys()
        assert all(span and span in text for spans in m["spans"].values() for span in spans)
        assert set(m["failures"]) | m["uncertain_release"].keys() <= set(config["release"])
        assert all(span and span in text for k in ("failures", "uncertain_release") for span in m[k].values())
        assert (len(text.split()) > config["caps"]["body_words"]) == ("body exceeds 90 words" in m["failures"])
        material = sum(rubric[k] for k, v in m["spans"].items() if v)
        passes = not (m["failures"] or m["uncertain_release"])
        checks[key] = {"points": material, "release": passes, "guarded_points": material if passes else 0,
                       "criteria": [k for k, v in m["spans"].items() if v],
                       "points_if_final_vote_inferred": material + (rubric["AF"] if "AF" in m["sensitivity"] else 0),
                       "points_if_literal_us_phrase_required": material - (
                           rubric["U"] if "U" in m["sensitivity"] else 0),
                       "release_failures": m["failures"], "uncertain_release": m["uncertain_release"],
                       "words": len(text.split()), "ended": row["ended"], "input_tokens": len(row["input_ids"]),
                       "output_tokens": len(row["output_ids"])}
    traced = load(annotations / "field-traces.json")
    for key, features in traced.items():
        note = json.loads(rows[key]["messages"][1]["content"])["supplement"]["text"]
        for source, final in features.values():
            assert source and source in note
            assert final is None or final in rows[key]["output"]
    worlds = {world: {arm: {**path, **checks[path["generation"]]} for arm, path in arms.items()}
              for world, arms in paths.items()}
    return {"verified_generations": len(rows), "worlds": worlds, "pooled": checks["pooled"],
            "verified_field_traces": sum(len(m) for m in traced.values())}


def score():
    requests, paths = plan()
    assert paths == load(HERE / "frozen-actions.json")
    return score_batch(EVIDENCE, FAMILY, requests, pins(), paths, HERE, masked)


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("mode", choices=("score", "records"))
    result = score() if cli.parse_args().mode == "score" else {
        key: load(PROTOCOL)["public"] + "\n\n" + row["output"] for key, row in read_rows(EVIDENCE).items()}
    print(json.dumps(result, ensure_ascii=False, indent=2))
