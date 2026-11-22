"""Review final workshop explanations under blinded, matched evidence."""
import argparse
import json
from pathlib import Path

import warrant_live_score as base
import warrant_reasons as study


def cases(rows):
    inputs = {}
    for key, roles, evidence, proof in study.all_views():
        table = study.logic(roles, evidence)
        for arm in ("certificate", "reasons"):
            name = f"{key}/{arm}"
            row = rows[name]
            parsed = base.parse(row["output"])
            if parsed is None:
                parsed = {"decision": None, "evidence": None, "memo": row["output"]}
            inputs[base.alias_for(name)] = {"case": key, "arm": arm, "candidate": parsed,
                                            "strict_json": parsed["decision"] is not None,
                                            "finished": row["ended"], "proof": proof, "facts": evidence, "table": table,
                                            "input_tokens": len(row["input_ids"]), "output_tokens": len(row["output_ids"])}
    return inputs


def score(inputs, marks):
    assert inputs.keys() == marks.keys()
    results = {}
    for alias, row in inputs.items():
        review = marks[alias]
        memo = row["candidate"]["memo"]
        for field in ("reason", "scope"):
            label, witness = review[field]
            assert label in ("met", "unmet", "uncertain")
            assert not witness or witness in memo
            assert witness or label != "met"
        assert all(span and span in memo for span in review["material_errors"])
        metrics = {"decision": row["candidate"]["decision"] in row["proof"]["permitted_decisions"],
                   "evidence": row["candidate"]["evidence"] == list(row["facts"]),
                   "reason": review["reason"][0] == "met", "scope": review["scope"][0] == "met"}
        words = len(memo.split())
        within = row["finished"] and words <= 90 and row["strict_json"]
        release = within and not review["material_errors"] and all(metrics.values())
        raw = sum(points * metrics[key] for key, points in (("decision", 25), ("evidence", 15),
                                                            ("reason", 20), ("scope", 10)))
        results.setdefault(row["case"], {})[row["arm"]] = {"alias": alias, "checked": metrics,
            "record_words": words, "within_format": within, "material_points": raw, "release_points": raw if release else 0,
            "strict_release": release, "review": review, "input_tokens": row["input_tokens"],
            "output_tokens": row["output_tokens"], "candidate": row["candidate"], "permitted": row["proof"]["permitted_decisions"]}
    return results


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("mode", choices=("blind", "score"))
    cli.add_argument("folder", type=Path)
    args = cli.parse_args()
    inputs = cases(study.verify(args.folder))
    if args.mode == "blind":
        output = {key: {k: v for k, v in item.items() if k not in ("case", "arm", "input_tokens", "output_tokens")}
                  for key, item in sorted(inputs.items())}
    else:
        marks = json.loads((args.folder / "review.json").read_text())
        output = score(inputs, marks)
    print(json.dumps(output, indent=2, ensure_ascii=False))
