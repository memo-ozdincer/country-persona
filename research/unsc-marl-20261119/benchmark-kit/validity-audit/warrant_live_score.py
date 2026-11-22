"""Score evidence transfer, certified decisions and final workshop prose."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import re

import warrant_live as study


def alias_for(key):
    return sha256(("warrant-live-review/" + key).encode()).hexdigest()[:8]


def parse(text):
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return None
    if (isinstance(data, dict) and data.keys() == {"decision", "evidence", "memo"}
            and isinstance(data["decision"], str) and isinstance(data["memo"], str)
            and isinstance(data["evidence"], list)):
        return data
    return None


def analyze(rows):
    finals = {}
    for key, roles, evidence, proof, _ in study.views(rows):
        row = rows[key]
        text = row["output"]
        strict = parse(text)
        fenced = re.fullmatch(r"```(?:json)?\s*(.*?)\s*```", text, re.S) if strict is None else None
        parsed = strict or (parse(fenced.group(1)) if fenced else None)
        if parsed is None:
            parsed = {"decision": None, "evidence": None, "memo": text}
        finals[alias_for(key)] = {"key": key, "roles": roles, "admitted_reports": evidence, "proof": proof,
                                  "finished": row["ended"], "strict_json": strict is not None, "parsed": parsed}
    return finals


def evaluate(rows, review):
    finals = analyze(rows)
    assert finals.keys() == review.keys()
    results = {}
    for alias, final in finals.items():
        marks = review[alias]
        memo = final["parsed"]["memo"]
        for axis in ("reason", "scope"):
            label, span = marks[axis]
            assert label in ("met", "unmet", "uncertain")
            assert not span or span in memo
            assert span or label != "met"
        for defect in marks["material_errors"]:
            assert defect and defect in memo
        permitted = final["proof"]["permitted_decisions"]
        correct = final["parsed"]["decision"] in permitted
        citations = final["parsed"]["evidence"] == list(final["admitted_reports"])
        reason = marks["reason"][0] == "met"
        scope = marks["scope"][0] == "met"
        points = 25 * correct + 15 * citations + 20 * reason + 10 * scope
        size = len(memo.split())
        release = (final["strict_json"] and final["finished"] and size <= 90 and not marks["material_errors"]
                   and correct and citations and reason and scope)
        results[final["key"]] = {"review_alias": alias, **{k: v for k, v in final.items() if k != "key"},
                                 "decision_correct": correct, "receipt_coverage": citations, "words": size,
                                 "material_points": points, "strict_complete": release,
                                 "release_points": points if release else 0, "review": marks}
    messages = {}
    for name, scenario in study.scenarios().items():
        opening = [study.admitted(rows, f"{name}/O{i}", fact) for i, fact in enumerate(scenario["moves"], 1)]
        fact, question = study.followup(rows, name, scenario)
        messages[name] = {"opening_exact": opening, "opening_delivered": study.opens(rows, name, scenario),
                          "request": question, "reply_exact": bool(fact and study.admitted(rows, f"{name}/reply", fact)),
                          "reply": fact if fact and study.admitted(rows, f"{name}/reply", fact) else None}
    return {"messages": messages, "finals": results}


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("mode", choices=("blind", "score"))
    cli.add_argument("directory", type=Path)
    cli.add_argument("--authorized-only", action="store_true")
    args = cli.parse_args()
    if args.authorized_only:
        import warrant_live_authorized as authorized

        rows = authorized.verify(args.directory)
    else:
        rows = study.verify(args.directory)
    if args.mode == "blind":
        result = {k: {name: value for name, value in row.items() if name != "key"}
                  for k, row in sorted(analyze(rows).items())}
    else:
        review = json.loads((args.directory / "review.json").read_text())
        result = evaluate(rows, review)
    print(json.dumps(result, ensure_ascii=False, indent=2))
