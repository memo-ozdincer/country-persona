"""Validate rubric votes and compare certified versus the frozen original finals."""
import argparse
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / "judge"))
from score import by_id, score


def report(base, grading):
    deck = by_id(json.loads((base / "deck.json").read_text()))
    keys = json.loads((base / "arm-key.json").read_text())
    original = json.loads((HERE.parent / "evidence" / "review" / "scores.json").read_text())["results"]
    verified = json.loads((base / "mechanical.json").read_text())
    verdicts = by_id(json.loads(grading.read_text())["verdicts"])
    assert deck.keys() == keys.keys() == verdicts.keys()
    result = {}
    for id_, packet in deck.items():
        name = keys[id_]
        _, arm, variant = name.split("-")
        old = original[variant][arm]
        new = score(packet, verdicts[id_])
        assert set(v["id"] for v in verdicts[id_]["units"]) == set(old["criteria"])
        for criterion in verdicts[id_]["units"]:
            assert criterion["id"] in old["criteria"]
        mechanically = verified[name]
        strict = {
            "before": old["semantic_strict"] and mechanically["old"]["exact_label_correct"]
                      and mechanically["old"]["at_most_130_words"],
            "after": new["strict"] and mechanically["certified"]["exact_label_correct"]
                     and mechanically["certified"]["at_most_130_words"],
        }
        changed = {u["id"]: [old["criteria"][u["id"]], u["status"]]
                   for u in verdicts[id_]["units"] if old["criteria"][u["id"]] != u["status"]}
        result[name] = {
            "before_70": old["semantic"], "after_70": new["final"],
            "before_guard": old["guard"], "after_guard": new["guard"],
            "full_contract": strict, "criterion_transitions": changed,
        }
    return result


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("review", type=Path)
    cli.add_argument("verdicts", type=Path)
    args = cli.parse_args()
    print(json.dumps(report(args.review, args.verdicts), indent=2))
