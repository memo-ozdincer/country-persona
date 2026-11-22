"""Score dated delegation positions and final memos under three discussion protocols.

Run from the project root with PYTHONPATH=src. Output is one JSON entry per event.
"""
import argparse
from collections import Counter
import json
from pathlib import Path

from country_persona.io import digest
from score_discussion_delta import transitions


def read_rows(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line]


def replay(transcript, annotations):
    reviews = {row["response_id"]: row for row in annotations}
    if len(reviews) != len(annotations) or len(transcript) != len(reviews):
        raise ValueError("Expected one review per response")
    groups = {}
    for row in transcript:
        review = reviews[row["response_id"]]
        if review["output_digest"] != digest(row["output"]) or review["case_sha256"] != row["case_sha256"]:
            raise ValueError("Response or prompt differs from the reviewed version")
        event = groups.setdefault(row["scenario_id"], {})
        key = row["country"], row["stage"], row["condition"]
        if key in event:
            raise ValueError("Repeated condition for this event and role")
        event[key] = row, review["ratings"]
    result = {}
    for name, event in groups.items():
        roles = sorted({country for country, stage, _ in event if stage == "initial"})
        out = {"roles": {}, "memos": {}, "total_generated_tokens": {}}
        for country in roles:
            solo, peer = "independent_revision", "peer_revision"
            opening, ratings = event[country, "initial", solo]
            other, other_ratings = event[country, "initial", peer]
            if opening["output"] != other["output"] or ratings != other_ratings:
                raise ValueError("Unequal opening texts or judgments")
            revisions = [event[country, "revision", arm][1] for arm in (solo, peer)]
            components = {}
            for category in ("content", "check"):
                arms = [{k: {"status": v} for k, v in scores.items() if f".{category}." in k}
                        for scores in (ratings, *revisions)]
                components[category] = transitions(*arms)
                components[category]["peer_endpoint"] = Counter(v["status"] for v in arms[-1].values())
            out["roles"][country] = components
        for (country, stage, arm), (row, ratings) in event.items():
            out["total_generated_tokens"][arm] = out["total_generated_tokens"].get(arm, 0) + row["generated_tokens"]
            if stage == "synthesis":
                out["memos"][arm] = ratings
        result[name] = out
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("transcript", type=Path)
    parser.add_argument("reviews", type=Path)
    args = parser.parse_args()
    print(json.dumps(replay(read_rows(args.transcript), read_rows(args.reviews)), indent=2))
