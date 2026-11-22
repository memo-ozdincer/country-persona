"""Bind exact and reviewed witnesses to prewritten evidence claims."""
import argparse
import json
from pathlib import Path

import facilitator_live_claims as study
import facilitator_live_writing_score as rubric

PUBLIC = {
    "unifil": (
        "On 31 August 2023 the Council adopted France's draft S/2023/641 as resolution 2695 (2023) "
        "by 13 votes in favour, none against and two abstentions, China and Russia [vote]. "
        "It renewed UNIFIL's existing mandate through 31 August 2024 and reaffirmed independent action within "
        "that mandate without prior permission, with continued coordination with Lebanon's Government "
        "under the status-of-forces agreement [operative]."
    ),
    "myanmar": (
        "The Council adopted draft S/2022/980 as resolution 2669 (2022) by 12 votes in favour, "
        "none against and three abstentions by China, India and Russia [vote]. "
        "It demanded an immediate end to violence, called for humanitarian access and acknowledged ASEAN's central role. "
        "It requested an oral report to the Council by 15 March 2023 from the Secretary-General or his Special Envoy, "
        "in coordination with the ASEAN Special Envoy, on UN support for the Five-Point Consensus [mandate]."
    ),
}
PUBLIC_UNITS = {
    "unifil": ("procedure", "disposition", "duration", "permission", "coordination"),
    "myanmar": ("draft-act", "vote-count", "humanitarian", "asean", "reporting", "authority"),
}
CLAUSES = {
    "unifil": (
        (("brazil-reason",), "Brazil said the draft preserved UNIFIL's freedom to operate and addressed some Lebanese concerns [brazil].", "brazil-reason"),
        (("china-reason",), "China said the text fell short on Lebanon's concerns and emphasized sovereignty and consent in peacekeeping [china].", "china-reason"),
        (("russia-reason",), "Russia attributed its abstention to late changes that lost an earlier compromise and continued to support UNIFIL's work [russia].", "russia-reason"),
        (("brazil-support", "china-support"), "Brazil and China both supported UNIFIL's work [brazil, china].", "overlap"),
        (("brazil-reason", "china-reason"), "Brazil saw some Lebanese concerns addressed. China found the response insufficient [brazil, china].", "open-issue"),
    ),
    "myanmar": (
        (("uk",), "The United Kingdom submitted the draft and voted in favour. It emphasized ending violence, humanitarian access and support for ASEAN [vote, uk].", "uk"),
        (("india",), "India abstained, citing neighbours' concerns and advocating quiet, constructive diplomacy [vote, india].", "india"),
        (("role",), "The Council President announced adoption. India's representative separately explained its national abstention [chair].", "role"),
        (("uk", "india"), "The UK highlighted ASEAN and India stressed regional concerns. The UK supported the text and India abstained [vote, uk, india].", "overlap"),
    ),
}


def items(rows):
    checks = study.items(study.old_rows())
    return {key: {**entry, "witness": rows[key]["output"], "ended": rows[key]["ended"]}
            for key, entry in checks.items()}


def literal(row):
    text = row["witness"]
    return row["ended"] and text != "NONE" and bool(text) and text in row["evidence"]


def record(name, sources, found, marks, reviewed):
    present = {key for key, value in found.items()
               if literal(value) and (not reviewed or marks[value["key"]]["supported"] == "met")}
    units = list(PUBLIC_UNITS[name])
    parts = [PUBLIC[name]]
    used = set()
    for keys, text, unit in CLAUSES[name]:
        if set(keys) <= present:
            parts.append(text)
            used.update(keys)
            units.append(unit)
    text = "\n\n".join(parts)
    assert rubric.citations(text) <= sources.keys()
    for unit in units:
        assert set(rubric.REQUIRED[name][unit]) <= sources.keys()
    points = 7 * len(units)
    guarded = len(text.split()) <= 175 and all(marks[found[k]["key"]]["supported"] == "met" for k in used)
    return {"text": text, "points": points, "release_points": points if guarded else 0, "strict": guarded and points == 70,
            "guarded": guarded, "used_claims": sorted(used), "units": units, "words": len(text.split())}


def run(rows, marks):
    checks = items(rows)
    assert checks.keys() == marks.keys()
    for key, review in marks.items():
        assert review["supported"] in ("met", "unmet", "uncertain") and review["reason"].strip()
        assert not review["span"] or review["span"] in checks[key]["witness"]
        if review["supported"] == "met":
            assert literal(checks[key]) and review["span"]
    by_view = {}
    for vid, name, _, sources, refs in study.previous.final_views(study.old_rows()):
        found = {}
        for key, check in checks.items():
            if vid in check["views"]:
                claim = key.split("/")[1]
                assert claim not in found
                found[claim] = {"key": key, **check}
        by_view[vid] = {"arms": refs, "literal": record(name, sources, found, marks, False),
                        "reviewed": record(name, sources, found, marks, True)}
    totals = {
        "witness_calls": len(checks),
        "literal_admissions": sum(literal(r) for r in checks.values()),
        "approved_witnesses": sum(m["supported"] == "met" for m in marks.values()),
        "released_views": {mode: sum(r[mode]["guarded"] for r in by_view.values()) for mode in ("literal", "reviewed")},
        "strict_views": {mode: sum(r[mode]["strict"] for r in by_view.values()) for mode in ("literal", "reviewed")},
    }
    return {"scope": "Source-local frozen-model witnesses and same-assistant semantic review. "
                     "The final uses prewritten claims and the original receipt masks.",
            "counts": totals, "views": by_view}


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("directory", type=Path)
    cli.add_argument("--marks", type=Path)
    args = cli.parse_args()
    rows = study.verify(args.directory)
    value = run(rows, json.loads(args.marks.read_text())) if args.marks else items(rows)
    print(json.dumps(value, indent=2, ensure_ascii=False))
