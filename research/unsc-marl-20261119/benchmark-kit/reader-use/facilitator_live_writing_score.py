"""Judge new Council prose with exact reviewed spans and paired source controls."""
import argparse
import json
from pathlib import Path
import re

import facilitator_live_writing as live

REQUIRED = {
    "unifil": {"procedure": ("vote",), "disposition": ("vote",), "duration": ("operative",),
               "permission": ("operative",), "coordination": ("operative",),
               "brazil-reason": ("brazil",), "china-reason": ("china",), "russia-reason": ("russia",),
               "overlap": ("brazil", "china"), "open-issue": ("brazil", "china")},
    "myanmar": {"draft-act": ("vote",), "vote-count": ("vote",), "uk": ("vote", "uk"),
                "india": ("vote", "india"), "role": ("chair",), "humanitarian": ("mandate",),
                "asean": ("mandate",), "overlap": ("uk", "india"), "reporting": ("mandate",),
                "authority": ()},
}
INLINE = re.compile(r"\[([^\[\]\n]+)\]")


def citations(text):
    return {part.strip() for group in INLINE.findall(text) for part in re.split(r"[,;]", group)}


def review_items(rows):
    return {
        "replies": {key: {"authorized": source, "text": rows[key]["output"], "ended": rows[key]["ended"]}
                    for key, _, _, _, source in live.tasks()},
        "finals": {key: {"docket": name, "sources": shown, "text": rows[key]["output"], "ended": rows[key]["ended"]}
                   for key, name, _, shown, _ in live.final_views(rows)},
    }


def grade(key, name, shown, raw, mark):
    assert set(mark) == {"met", "guard", "guard_reason"}
    assert mark["guard"] in ("clear", "failed", "uncertain") and mark["guard_reason"].strip()
    text = raw["output"]
    needs = REQUIRED[name]
    assert mark["met"].keys() <= needs.keys()
    for criterion, span in mark["met"].items():
        assert span and span in text and set(needs[criterion]) <= shown.keys(), (key, criterion, span)
    missing = [k for k, span in mark["met"].items() if not set(needs[k]) <= citations(span)]
    off_view = sorted(citations(text) - shown.keys())
    points = 7 * len(mark["met"])
    guarded = raw["ended"] and len(text.split()) <= 175 and mark["guard"] == "clear" and not off_view
    return {"points": points, "release_points": points if guarded else 0, "guarded": guarded,
            "strict": guarded and points == 70 and not missing, "missing_inline_citations": missing,
            "off_view_citations": off_view, "ended": raw["ended"], "words": len(text.split()),
            "met": sorted(mark["met"]), "input_tokens": len(raw["input_ids"]), "output_tokens": len(raw["output_ids"])}


def run(rows, marks):
    items = review_items(rows)
    assert marks.keys() == items.keys()
    assert all(marks[k].keys() == items[k].keys() for k in marks)
    tables = {}
    for key, name, _, shown, refs in live.final_views(rows):
        tables[key] = grade(key, name, shown, rows[key], marks["finals"][key])
        tables[key]["applies_to"] = refs
    for key, review in marks["replies"].items():
        assert review["support"] in ("met", "uncertain", "unmet") and review["reason"].strip()
        assert not review["span"] or review["span"] in rows[key]["output"]
    cases, solo = {}, {}
    for key, _, _, sources, refs in live.final_views(rows):
        for arm in refs:
            if arm["mode"] == "pooled":
                solo[key] = tables[key]
                continue
            label = f"{key.rsplit('/', 2)[0]}/{arm['arm']}"
            option = {"id": key, "sources": sorted(sources), **tables[key]}
            cases.setdefault(label, {})[arm["mode"]] = option
    for name, case in cases.items():
        assert set(case) == {"live", "direct"}
    totals = {"physical_calls": len(rows), "actual_reply_calls": len(items["replies"]),
              "actual_final_calls": len(items["finals"]), "logical_route_calls_on_this_stage": 24,
              "logical_direct_final_calls": 12, "logical_solo_calls": 2,
              "reply_support_met": sum(v["support"] == "met" for v in marks["replies"].values())}
    return {"scope": "Same-assistant exact-span assessment. Matched routes reuse the prior decoder, "
                     "generate new language replies, and write new final prose. Source-direct is a component control.",
            "totals": totals, "cases": cases, "solo": solo, "reviewed_finals": tables}


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("directory", type=Path)
    p.add_argument("--marks", type=Path)
    args = p.parse_args()
    rows = live.verify(args.directory)
    value = run(rows, json.loads(args.marks.read_text())) if args.marks else review_items(rows)
    print(json.dumps(value, ensure_ascii=False, indent=2))
