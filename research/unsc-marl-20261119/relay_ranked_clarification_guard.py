"""Require a literal, compatible source span before changing a ranked receipt."""
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import re
import sys

import relay_ranked_clarification as clarify

GRADE = ((3, ("strongest choice", "above all")), (2, ("second choice",)), (1, ("fallback",)))


def has(text, phrase):
    return re.search(r"\b" + re.escape(phrase) + r"\b", text) is not None


def span_matches(package, clause, shared):
    text = clause.lower()
    scope = package["scope"]
    if not (has(text, scope) or has(shared, scope)):
        return False
    if "explicit_consent" in package:
        if not package["explicit_consent"] or "require explicit host consent" not in shared:
            return False
        return has(text, package["coordination"] + " coordination")
    if not has(text, package["instrument"]):
        return False
    if not (has(text, package["forum"]) or has(shared, package["forum"])):
        return False
    return has(text, "with a review" if package["review"] else "without a review")


def verify(mandate, package, proposed):
    segments = [span.strip() for span in re.split(r"[.,]|\band (?=[^.]*?(?:strongest choice|second choice|fallback))", mandate)
                if span.strip()]
    source_constraints = [segment for segment in segments
                          if segment.lower().startswith(("require ", "use ", "limit "))]
    shared = " ".join(segment.lower() for segment in source_constraints)
    good = []
    for span in segments:
        candidates = {value for value, names in GRADE if any(has(span.lower(), n) for n in names)}
        if candidates == {proposed} and span_matches(package, span, shared):
            good.append(span)
    return [good[0], *source_constraints] if len(good) == 1 else []


def verified_update(task, current, verified_profile, seat):
    ids = (task.first, task.second)
    selected = list(current)
    selected[seat] = ids[seat][verified_profile]
    return tuple(selected)


def run(source):
    report = json.loads(source.read_text())
    tasks = clarify.mandate.language.ranked.fixtures()
    packages = {family: json.loads(path.read_text())["options"]
                for family, path in zip(tasks, clarify.mandate.language.ranked.FILES, strict=True)}
    from relay_ranked_mandates_audit import answered
    rows = []
    for family, task in tasks.items():
        for episode in report["outcomes"][family]:
            baseline = episode["arms"]["no_query/none"]
            for strategy in ("relay_only", "far_only", "lowest_margin"):
                selected = episode["arms"][strategy+"/consensus"]
                question, reply, seat = selected["question"], selected["reply"], selected["query_seat"]
                private = question["key"][2]
                current = tuple(baseline["received"])
                spans = []
                revision = None if reply is None else reply["revision"]
                if revision is not None and revision != question["claimed"]:
                    text = clarify.mandate.MANDATES[family][seat][private]
                    package = packages[family][question["package_index"]]
                    spans = verify(text, package, reply["grade"])
                    assert all(span in text for span in spans)
                    if spans:
                        current = verified_update(task, current, revision, seat)
                world = episode["world"]
                truth = tuple(v if v == t else 0 for v, t in zip(current, world, strict=True))
                warrant = answered(task, *truth)
                visible = answered(task, *current)
                # Use the same complete-view readout as the unguarded replay.
                # A source-backed update changes only the one targeted card.
                choice = selected["choice"] if spans else baseline["choice"]
                assert choice in visible
                rows.append({"family": family, "world": world, "strategy": strategy,
                             "question": question, "supporting_spans": spans, "after": current,
                             "false_cards": sum(bool(v) and v != t for v, t in zip(current, world, strict=True)),
                             "choice": choice, "warrant": sorted(warrant),
                             "completed": choice in warrant and choice != "unresolved",
                             "unsupported": choice not in warrant and choice != "unresolved"})
    counts = {}
    for row in rows:
        counter = counts.setdefault(row["strategy"], Counter())
        for metric in ("false_cards", "completed", "unsupported"):
            counter[metric] += row[metric]
        counter["accepted_updates"] += bool(row["supporting_spans"])
    return {"reply_report_sha256": sha256(source.read_bytes()).hexdigest(), "rows": rows, "counts": counts}


if __name__ == "__main__":
    print(json.dumps(run(Path(sys.argv[1])), indent=2))
