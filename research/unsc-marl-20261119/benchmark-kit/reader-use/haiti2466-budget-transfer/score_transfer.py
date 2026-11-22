"""Audit the new live bodies and their frozen source paths."""
import argparse
from hashlib import sha256
import json
import sys

from run_transfer import EVIDENCE, FAMILY, HERE, PACKET, pins, prompts, read
sys.path.insert(0, str(HERE.parent / "bosnia2604-routing/protected-record"))
from score_protected import read_rows, verify_generation


def masked(key):
    return sha256(("2466-transfer/" + key).encode()).hexdigest()[:10]


def assess(row, grade, source, packet):
    rubric = {atom["id"]: atom["points"] for c in packet["cards"] for atom in c["atoms"]}
    rubric[packet["joint"]["id"]] = packet["joint"]["points"]
    body = row["output"]
    assert grade["spans"].keys() == rubric.keys()
    assert all(span and span in body for spans in grade["spans"].values() for span in spans)
    assert set(grade["uncertain_criteria"]) <= {k for k,v in grade["spans"].items() if not v}
    assert set(grade["failures"]) | grade["uncertain_release"].keys() <= set(packet["release"])
    assert all(span and span in body for field in ("failures", "uncertain_release")
               for span in grade[field].values())
    words = len(body.split())
    assert (words > 70) == ("body over 70 words" in grade["failures"])
    available = set(source["ids"])
    for k in (packet["joint"]["id"],):
        if set(packet["joint"]["needs"]) <= available:
            available.add(k)
    met = {k for k, v in grade["spans"].items() if v}
    points = sum(rubric[k] for k in met)
    passed = row["ended"] and not (grade["failures"] or grade["uncertain_release"])
    assert not (met - available) or not passed
    return {"points": points, "release": passed, "guarded_points": points if passed else 0,
                  "retained_available_points": sum(rubric[k] for k in met & available),
                  "available_points": sum(rubric[k] for k in available), "coverage_gaps": sorted(available - met),
                  "credited_without_received_support": sorted(met - available), "criteria": sorted(met),
                  "uncertain_criteria": grade["uncertain_criteria"], "failures": grade["failures"],
                  "uncertain_release": grade["uncertain_release"], "body_words": words,
                  "input_words_with_labels": source["words"], "input_tokens": len(row["input_ids"]),
                  "output_tokens": len(row["output_ids"]), "ended": row["ended"]}


def score(rows):
    expected, routes = prompts()
    assert json.loads(json.dumps(routes)) == read(HERE / "generation-paths.json")
    verify_generation(EVIDENCE, rows, expected, FAMILY, pins())
    marks = read(HERE / "marks.json")
    assert marks.keys() == {masked(k) for k in rows} and len(rows) == 4
    packet = read(PACKET)
    cases = {k: assess(row, marks[masked(k)], routes["catalog"][k], packet) for k, row in rows.items()}
    paths = {}
    for world, arms in routes["paths"].items():
        paths[world] = {arm: dict(path) for arm, path in arms.items()}
        for path in paths[world].values():
            path["guarded_by_writer_input"] = {m: cases[path[m]]["guarded_points"] for m in ("selected", "all")}
    return {"verified_outputs": len(rows), "records": cases, "worlds": paths, "pooled": routes["pooled"]}


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("mode", choices=("score", "deck", "records"))
    mode = cli.parse_args().mode
    rows = read_rows(EVIDENCE)
    if mode == "score":
        result = score(rows)
    elif mode == "deck":
        result = dict(sorted((masked(k), v["output"]) for k,v in rows.items()))
    else:
        public = read(PACKET)["public"]
        result = {k: public + "\n\n" + row["output"] for k, row in rows.items()}
    print(json.dumps(result,ensure_ascii=False,indent=2))
