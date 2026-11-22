"""Build an arm-free record deck and score evidence-grounded annotations."""
import argparse
from hashlib import sha256
import json
from pathlib import Path

from source_record_episode import ARMS, PACK

PREFIX = {"disposition": "D", "operative_action": "A", "positions_and_reasons": "P",
          "overlap_and_open_issues": "C", "authority_and_scope": "S"}


def bundle(directory):
    cases = {r["family"]: r for r in json.loads(PACK.read_text())["cases"]}
    finals = json.loads((directory / "final-records.json").read_text())
    items, join = {}, {}
    for name, records in finals.items():
        case = cases[name]
        evidence = {**case["docket"], **{k: v for role in case["delegate_evidence"].values() for k, v in role.items()}}
        units = {PREFIX[group] + str(index): text for group, pair in case["criterion_pairs"].items()
                 for index, text in enumerate(pair, 1)}
        for run, answer in records.items():
            key = sha256(("source-record-review/" + run).encode()).hexdigest()[:10]
            items[key] = {"family": name, "evidence": evidence, "criteria": units, "candidate": answer}
            join[key] = run
    return dict(sorted(items.items())), join


def score(directory, annotation):
    items, join = bundle(directory)
    assert set(items) == set(annotation["reviews"])
    scores = {}
    for key, item in items.items():
        review = annotation["reviews"][key]
        assert set(review["units"]) == set(item["criteria"])
        checks = [*review["units"].values(), review["guard"]]
        for status, note, span, references in checks:
            assert note and all(quote and quote in item["evidence"][block] for block, quote in references)
            assert not span or span in item["candidate"], (key, span)
            if status in ("met", "failed"):
                assert span and references
        values = [status for status, *_ in review["units"].values()]
        assert set(values) <= {"met", "unmet", "uncertain"}
        assert review["guard"][0] in ("clear", "failed", "uncertain")
        scores[join[key]] = {"floor": 7 * values.count("met"), "ceiling": 7 * (len(values) - values.count("unmet")),
                             "critical_guard": review["guard"][0], "words": len(item["candidate"].split())}
    for value in scores.values():
        value["under_limit"] = value["words"] <= 160
    return scores


def budgets(directory):
    records = {r["id"]: r for r in map(json.loads, (directory / "transcript.jsonl").read_text().splitlines())}
    cases = json.loads((directory / "final-records.json").read_text())
    totals = {}
    for family in cases:
        for arm in ARMS:
            stages = [records[f"{family}/{arm}/chair"], *(records[f"{family}/{arm}/revision_{i}"] for i in (1, 2))]
            prefix = "pooled_solo" if arm == "pooled_solo" else "common"
            stages.extend(records[f"{family}/{prefix}/opening_{i}"] for i in (1, 2))
            totals[f"{family}/{arm}"] = {
                "input_tokens": sum(len(r["input_ids"]) for r in stages),
                "output_tokens": sum(len(r["output_ids"]) for r in stages),
                "output_ceiling": sum(r["cap"] for r in stages),
                "caps_hit": sum(not r["ended"] for r in stages),
            }
    return totals


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("directory", type=Path)
    cli.add_argument("--annotations", type=Path)
    args = cli.parse_args()
    if args.annotations:
        annotations = json.loads(args.annotations.read_text())
        value = {"scope": annotations["scope"], "final": score(args.directory, annotations), "budgets": budgets(args.directory)}
    else:
        value = bundle(args.directory)[0]
    print(json.dumps(value, indent=2, ensure_ascii=False))
