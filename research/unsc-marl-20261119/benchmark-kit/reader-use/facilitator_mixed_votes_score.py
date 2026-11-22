"""Score stage and actor binding and replay the previously frozen routers."""
import argparse
from collections import Counter
from itertools import product
import json
from pathlib import Path
from unittest.mock import patch

import facilitator_mixed_votes as study
import facilitator_new_meetings_score as prior
import facilitator_receipt_search as search

MODES = ("combined_literal", "combined_bound", "isolated_bound", "roll_call")
PAIRS = {
    "space": (("China", "Russian Federation", "yes"), ("Switzerland", "Japan", "abstain")),
    "gaza": (("United States", "China", "yes"), ("Brazil", "France", "abstain")),
}


def admission(row, source):
    label, delimiter, span = row["output"].partition(",")
    label = label.strip().casefold()
    span = span.strip()
    if row["ended"] and delimiter and label in study.POLARITIES and span and span in source:
        return label, span
    return "unknown", None


def readings(rows):
    out = {}
    for key, actor, document, source, expected, line in study.records():
        row = rows[key]
        label, span = admission(row, source)
        # The stage, polarity and actor have to coexist within one exact line.
        # This does not consult the expected polarity from the fixture.
        bound = "unknown"
        if span:
            lead, separator, names = span.partition(": ")
            if (separator and lead == f"{document} {study.POLARITIES[label]}"
                    and actor in names.removesuffix(".").split(", ") and "\n" not in names
                    and span in source.splitlines()):
                bound = label
        out[key] = {"expected": expected, "expected_line": line, "raw": row["output"], "literal": label,
                    "bound": bound, "span": span, "correct_span": line == span,
                    "input_tokens": len(row["input_ids"]), "output_tokens": len(row["output_ids"])}
    return out


def relation(observed, claimed):
    if observed == "unknown":
        return "unknown"
    return "supports" if observed == claimed else "contradicts"


def truth(actor, record):
    label, = [p for p in study.POLARITIES if actor in record[p]]
    return label


def response(actors, document, kind, labels, seen, predicted):
    phrases = {"yes": "voted in favour of", "no": "voted against", "abstain": "abstained on"}
    action = []
    for i, (actor, label) in enumerate(zip(actors, labels, strict=True)):
        if i not in seen or label == "unknown":
            action.append(f"The available vote evidence does not establish how {actor} voted.")
        else:
            action.append(f"{actor} {phrases[label]} {kind} {document}. [S{i+1}]")
    return f"{predicted} | {' '.join(action)}"


def receipts(reads):
    outcomes, cases = {}, []
    for family, meeting in study.meetings().items():
        for record, (one, two, claimed) in product(meeting["records"], PAIRS[family]):
            document = record["id"]
            actors = (one, two)
            voted = tuple(truth(actor, record) for actor in actors)
            gold = tuple(relation(label, claimed) for label in voted)
            panel = "/".join((family, document.replace("/", "-"), f"{one}-{two}"))
            for mode in MODES:
                if mode == "roll_call":
                    shown, evidenced = voted, voted
                else:
                    arm, admission_rule = mode.split("_")
                    keys = [f"{family}/{document.replace('/', '-')}/{actor.replace(' ', '-')}/{arm}"
                            for actor in actors]
                    shown = tuple(reads[key][admission_rule] for key in keys)
                    evidenced = tuple(reads[key]["bound"] for key in keys)
                observed = tuple(relation(label, claimed) for label in shown)
                for bits in product((False, True), repeat=2):
                    seen = frozenset(i for i, bit in enumerate(bits) if bit)
                    expected = prior.base.decision(gold, seen)
                    predicted = prior.base.decision(observed, seen)
                    correct_fields = all(shown[i] == voted[i] for i in seen)
                    bound_fields = all(shown[i] == evidenced[i] for i in seen)
                    strict = correct_fields and bound_fields and expected == predicted
                    caption = response(actors, document, record["kind"], shown, seen, predicted)
                    cases.append((panel, mode, seen, observed, expected, predicted, strict))
                    outcomes[f"{panel}/{mode}/{2 * bits[0] + bits[1]}"] = {
                        "observed": shown, "recorded": voted, "bound": evidenced, "claimed_vote": claimed,
                        "seen": sorted(seen), "expected": expected, "predicted": predicted, "strict": strict,
                        "correct_fields": correct_fields, "bound_fields": bound_fields,
                        "false_action": predicted != "withhold" and expected != predicted,
                        "response": caption,
                    }
    return prior.policy.collect(cases), outcomes


def reading_summary(reads):
    summary = {}
    for key, row in reads.items():
        family, _, _, arm = key.split("/")
        for bucket in (arm, f"{family}/{arm}"):
            c = summary.setdefault(bucket, Counter())
            c.update({"rows": 1, "literal_right": row["literal"] == row["expected"],
                      "literal_wrong": row["literal"] not in ("unknown", row["expected"]),
                      "bound_right": row["bound"] == row["expected"], "exact_complete_evidence": row["correct_span"],
                      "input_tokens": row["input_tokens"], "output_tokens": row["output_tokens"]})
    return summary


def score(directory):
    rows = study.verify(directory)
    reads = readings(rows)
    bank, details = receipts(reads)
    frozen, independent = prior.ceiling.stock()
    systems = (("frozen", "learned", frozen), ("erased", "learned_erased", frozen),
               ("trained_independent", "learned_erased", independent), ("greedy", "greedy", {}))
    search.check()
    routing = {}
    with patch.object(prior.policy, "MODES", MODES):
        for layout in ("split", "overlap"):
            scores = prior.policy.evaluate(bank, systems, layout)
            upper = {}
            for mode in MODES:
                cohort = {key: row for key, row in bank.items() if key[1] == mode}
                certificate = {}
                for name, ack in (("independent", False), ("adaptive", True)):
                    _, _, grid = prior.ceiling.tensor(cohort, layout, ack)
                    certificate[name] = search.maximize(grid)
                assert certificate["adaptive"]["exact_net"] + 1e-10 >= max(
                    certificate["independent"]["exact_net"], scores["frozen"]["summary"][mode]["brief_net"])
                upper[mode] = certificate
            routing[layout] = {"policies": scores, "upper_bounds": upper}
    files = (Path(__file__), Path(search.__file__), study.PACK, directory / "launch.json", directory / "transcript.jsonl")
    return {"scope": "Two observed meetings with two vote targets each. Vote-group tables use normalized member names "
                     "and repeated stage anchors. The isolated arm receives the target block only. Exact receipt replay "
                     "uses compiled vote fields, previously frozen policies, and zero optimizer updates. Strict validates "
                     "only vote attribution and documentary disposition for this diagnostic.",
            "verified_generations": len(rows), "reader_summary": reading_summary(reads), "readings": reads,
            "receipts": details, "routing": routing, "sha256": {p.name: study.runner.digest(p) for p in files}}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    print(json.dumps(score(parser.parse_args().directory), indent=2, ensure_ascii=False))
