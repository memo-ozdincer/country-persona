"""Score exact evidence spans and compare neighboring receipt views."""
import argparse
from hashlib import sha256
from itertools import product
import json
from pathlib import Path

import facilitator_free_record_bank as study

EVIDENCE = study.EVIDENCE
KEYS = ("P1", "P2", "P3", "P4", "P5", "P6", "E", "C", "R", "X")
MASKS = (0, 0, 0, 0, 0, 0, 1, 2, 4, 6)


def blind(rows):
    result = {}
    for i in range(8):
        raw = rows[str(i)]
        alias = sha256(f"2699-free-review:{i}".encode()).hexdigest()[:8]
        packet = json.loads(raw["messages"][-1]["content"])
        result[alias] = {"candidate": raw["output"], "finished": raw["ended"],
                         "eligible": [k for k, m in zip(KEYS, MASKS, strict=True) if i & m == m],
                         "evidence": packet, "mask": i, "input_tokens": len(raw["input_ids"]),
                         "output_tokens": len(raw["output_ids"])}
    return dict(sorted(result.items()))


def score(rows, judgments):
    candidates = blind(rows)
    assert candidates.keys() == judgments.keys()
    material, released = [0] * 8, [0] * 8
    records = {}
    for key, row in candidates.items():
        notes = judgments[key]
        assert notes["criteria"].keys() == set(row["eligible"])
        passed = 0
        for label, witness in notes["criteria"].values():
            assert label in ("met", "unmet", "uncertain")
            assert not witness or witness in row["candidate"]
            assert witness or label != "met"
            passed += label == "met"
        assert all(w and w in row["candidate"] for w in notes["material_errors"])
        words = len(row["candidate"].split())
        clean = row["finished"] and words <= 285 and not notes["material_errors"]
        mask = row["mask"]
        material[mask] = 7 * passed
        released[mask] = material[mask] if clean else 0
        records[str(mask)] = {**row, "words": words, "review_alias": key, "review": notes, "releasable": clean,
                              "material_points": material[mask], "release_points": released[mask]}
    edges = []
    for a, i in product(range(8), (1, 2, 4)):
        if a & i:
            continue
        b = a | i
        edges.append({"before": a, "after": b, "material_gain": material[b] - material[a],
                      "release_gain": released[b] - released[a]})
    return {"material_bank": material, "released_bank": released, "records": records, "lattice_edges": edges}


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("mode", choices=("blind", "score"))
    cli.add_argument("directory", type=Path)
    args = cli.parse_args()
    rows = study.verify(args.directory)
    if args.mode == "blind":
        output = {key: {k: v for k, v in value.items() if k in ("candidate", "finished", "eligible", "evidence")}
                  for key, value in blind(rows).items()}
    else:
        output = score(rows, json.loads((EVIDENCE / "review.json").read_text()))
    print(json.dumps(output, ensure_ascii=False, indent=2))
