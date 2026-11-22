"""Reassemble each matched view from its newly transmitted, reviewed claim evidence."""
import argparse
import json
from pathlib import Path

import facilitator_claim_requests as study
import facilitator_live_claims_score as renderer


def run(rows, marks):
    previous = json.loads(study.PAIR_SCORE.read_text())["reassembled"]["views"]
    views = {key: (name, sources) for key, name, _, sources, _ in
             study.claims.previous.final_views(study.claims.old_rows())}
    cases = {}
    assert rows.keys() == marks.keys()
    for key, question, authorized in study.cases():
        sid, variant = key.split("/")
        name, view, *_ = study.TARGET[sid]
        mark = marks[key]
        response = rows[key]["output"]
        supported = mark["support"] == "met"
        assert mark["support"] in ("met", "unmet", "uncertain") and mark["reason"].strip()
        assert mark["spans"].keys() <= {k for k, (s, _) in study.claims.RULES[name].items() if s == sid}
        assert all(span and span in response for span in mark["spans"].values())
        if variant == "withheld":
            assert not ({"china-support", "uk"} & mark["spans"].keys()), "source-withheld guard rejected the claim"
        kept = previous[view]["reviewed"]["used_claims"]
        found = {}
        labels = {}
        for claim in kept:
            src = study.claims.RULES[name][claim][0]
            if src == sid:
                continue
            evidence = views[view][1][src]
            found[claim] = {"key": claim, "witness": evidence, "ended": True, "evidence": evidence}
            labels[claim] = {"supported": "met"}
        admitted = supported and rows[key]["ended"] and len(response.split()) <= 52
        if admitted:
            for claim, span in mark["spans"].items():
                found[claim] = {"key": claim, "witness": span, "ended": True, "evidence": response}
                labels[claim] = {"supported": "met"}
        shown = {**views[view][1], sid: response if admitted else ""}
        record = renderer.record(name, shown, found, labels, True)
        cases[key] = {"question": question, "authorized": authorized, "reply": response, "admitted": admitted,
                      "original_release_points": previous[view]["reviewed"]["release_points"],
                      "annotation": mark, "record": record, "input_tokens": len(rows[key]["input_ids"]),
                      "output_tokens": len(rows[key]["output_ids"])}
    return {"scope": "Two exposed, targeted response repairs with matched way to release each original branch. "
                     "The source-local review supplies exact supporting spans. No new optimizer update.",
            "actual_calls": len(rows), "cases": cases}


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("directory", type=Path)
    p.add_argument("--marks", required=True, type=Path)
    args = p.parse_args()
    print(json.dumps(run(study.verify(args.directory), json.loads(args.marks.read_text())),
                     ensure_ascii=False, indent=2))
