"""Count verified clause ideas and package consequences separately in typed traces."""
import argparse
from collections import Counter
import json
from pathlib import Path


def process(path):
    rows = json.loads(path.read_text())["paths"]
    episodes, group = {}, {}
    for key, trace in rows.items():
        counts, ideas, signs = Counter(), set(), set()
        for event in trace["events"]:
            role = event["claim"]["role"] if "claim" in event else event["role"]
            kind = event["type"]
            assert event["slot"] < 0 or event["slot"] < trace["slots"]
            counts[role, "opening_attempts" if event["slot"] < 0 else "slots"] += 1
            if kind == "check_scope":
                counts[role, "private_checks"] += 1
            if "claim" not in event:
                continue
            counts[role, "public_attempts"] += 1
            if not event["admitted"]:
                counts[role, "rejected_attempts"] += 1
                continue
            counts[role, "admitted_public_turns"] += 1
            added = {(role, stance, label) for stance in ("accepts", "excludes")
                     for label in event["claim"][stance]}
            if kind == "scope":
                ideas.add((role, "scope", tuple(sorted(label for _, _, label in added))))
                counts[role, "scope_publications"] += 1
            else:
                ideas.update((r, stance, (label,)) for r, stance, label in added - signs)
            counts[role, "new_package_signs"] += len(added - signs)
            signs |= added
        for role, _, _ in ideas:
            counts[role, "distinct_admitted_ideas"] += 1
        episodes[key] = {"/".join(k): val for k, val in sorted(counts.items())}
        arm = key.rsplit("/", 1)[0]
        group.setdefault(arm, Counter()).update(counts)
    return {"scope": "Typed protocol only. Each scope publication is a single source-level idea. Signs entailed by its publication are counted separately. No free-text semantic or causal peer score.",
            "episodes": episodes,
            "aggregate": {tag: {"/".join(key): val for key, val in sorted(counts.items())}
                          for tag, counts in group.items()}}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("metrics", type=Path)
    print(json.dumps(process(parser.parse_args().metrics), indent=2))
