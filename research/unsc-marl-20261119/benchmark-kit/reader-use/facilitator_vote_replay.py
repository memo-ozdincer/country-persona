"""Compare supplied and extracted vote facts against the archived prose pipeline."""
import argparse
from collections import Counter
import csv
import json
from pathlib import Path
from unittest.mock import patch

import facilitator_new_meetings_score as prior
import facilitator_receipt_search as search
from facilitator_scope_rules import VOTE_CLAIM
import facilitator_vote_channel as typed
import facilitator_vote_channel_format as revised

ARCHIVE = typed.HERE / "facilitator-new-meetings-evidence"
OFFICIAL_VOTES = {
    ("Ghana", "2634 (2022)"): "yes",
    ("China", "2634 (2022)"): "yes",
    ("United Kingdom", "2796 (2025)"): "yes",
    ("Algeria", "2796 (2025)"): "yes",
}
POSITIONS = {"voted in favour of": "yes", "voted in favor of": "yes", "voted against": "no", "abstained on": "abstain"}
MODES = ("literal", "verified_only", "official_labels", "official_compiled", "extracted_compiled",
         "normalized_extraction", "official_verified_open")


def vote_fields(label, claimed, actor, resolution):
    if label not in typed.VOTES:
        return "unknown", f"The available evidence does not establish how {actor} voted on resolution {resolution}."
    action = "supports" if label == claimed else "contradicts"
    vote = typed.VOTES[label]
    verb = f"voted {vote}" if vote else "abstained on"
    return action, f"{actor} {verb} resolution {resolution}."


def input_state():
    transcript = ARCHIVE / "transcript.jsonl"
    complete = prior.study.chair.load(ARCHIVE / "complete.json")
    assert complete["transcript_sha256"] == typed.prior.runner.digest(transcript)
    rows = {row["id"]: row for row in map(json.loads, transcript.read_text().splitlines())}
    assert len(rows) == complete["records"] == 36
    notes = prior.annotate(ARCHIVE, rows)
    reads = prior.read_relations(rows)
    return rows, notes, reads


def intervene(rows, notes, base_reads, extracted, mode):
    changed = {}
    outputs, marks = dict(rows), dict(notes)
    for key, actor, claim, _, _ in prior.study.source_rows():
        old = base_reads[key]
        open_text = "verified_only" if mode in ("official_verified_open", "verified_only") else "literal"
        relation = old[open_text]
        vote_claim = VOTE_CLAIM.fullmatch(claim)
        if vote_claim and mode not in ("literal", "verified_only"):
            resolution = vote_claim["res"]
            family = key.split("-", 1)[0]
            control = f"{family}/{key.rsplit('/', 1)[1]}"
            fact = extracted[control]
            assert fact["actor"] == actor == vote_claim["actor"] and fact["resolution"] == resolution
            if mode == "extracted_compiled":
                label = fact["admitted"]
            elif mode == "normalized_extraction":
                label = fact["normalized"]
            else:
                label = OFFICIAL_VOTES.get((actor, resolution))
            relation, text = vote_fields(label, POSITIONS[vote_claim["force"]], actor, resolution)
            if mode != "official_labels":
                field = f"{key}/field"
                outputs[field] = {"output": text, "ended": True}
                marks[field] = {"s1": text if label in typed.VOTES else "", "s2": "", "issue": "", "reason": ""}
        changed[key] = {mode: relation}
    with patch.object(prior, "MODES", (mode,)):
        grades = prior.grade(outputs, marks, changed)
        bank = prior.bank(changed, grades)
    route_grades = {key: row for key, row in grades.items() if key.endswith(f"/{mode}")}
    return changed, route_grades, bank


def policies(bank):
    fitted, independent = prior.ceiling.stock()
    baselines = (("frozen", "learned", fitted), ("erased", "learned_erased", fitted),
                 ("trained_independent", "learned_erased", independent), ("greedy", "greedy", {}))
    with patch.object(prior.policy, "MODES", MODES):
        return {inventory: prior.policy.evaluate(bank, baselines, inventory) for inventory in ("split", "overlap")}


def summaries(grades):
    grouped = {}
    for key, row in grades.items():
        panel, mask, mode = key.split("/")
        task = "speech" if panel.endswith("-2") else "vote"
        receipts = "both" if mask == "3" else ("none" if mask == "0" else "one")
        slot = grouped.setdefault(f"{mode}/{task}/{receipts}", Counter())
        slot.update({"briefs": 1, "correct": row["expected"] == row["disposition"], "strict": row["strict"],
                     "points": row["points"], "false_action": row["false_action"]})
    return grouped


def controls():
    for observed in (*typed.VOTES, "unknown"):
        for claimed in typed.VOTES:
            got, text = vote_fields(observed, claimed, "Ghana", "2634 (2022)")
            expected = ("unknown" if observed == "unknown" else
                        "supports" if observed == claimed else "contradicts")
            assert got == expected and "Ghana" in text and "2634 (2022)" in text


def normalize_vote(row, source):
    strict, span = typed.value(row, source)
    if strict != "unknown":
        return strict, span
    label, separator, remainder = row["output"].partition(",")
    label = label.strip().casefold()
    quote = remainder.strip()
    if row["ended"] and separator and label in typed.VOTES and quote and quote in source:
        return label, quote
    return "unknown", None


def read_witness_review(directory, extraction):
    with (directory / "witness-review.tsv").open(newline="") as f:
        records = list(csv.DictReader(f, delimiter="\t"))
    indexed = {r["id"]: r for r in records}
    assert len(indexed) == len(records) and indexed.keys() == extraction.keys()
    for key, row in extraction.items():
        mark = indexed[key]
        assert mark["span"] == (row["normalized_span"] or "")
        assert mark["adequate"] in ("yes", "no", "none")
        assert (mark["adequate"] == "none") == (row["normalized_span"] is None)
        assert (mark["adequate"] == "no") == bool(mark["issue"])
    return indexed


def bounds(banks, previous, replayed):
    search.check()
    result = {}
    for mode in ("literal", "official_compiled", "official_verified_open"):
        cohort = {key: row for key, row in banks.items() if key[1] == mode}
        exact = {}
        for layout in ("split", "overlap"):
            results = {}
            for name, acknowledgment in (("independent", False), ("adaptive", True)):
                _, _, payoff = prior.ceiling.tensor(cohort, layout, acknowledgment)
                results[name] = search.maximize(payoff)
                if mode == "literal":
                    archived = previous["routing"][layout]["upper_bounds"][mode][name]["exact_net"]
                    assert abs(results[name]["exact_net"] - archived) < 1e-10
            frozen = replayed[layout]["frozen"]["summary"][mode]["brief_net"]
            assert results["adaptive"]["exact_net"] + 1e-10 >= max(frozen, results["independent"]["exact_net"])
            exact[layout] = results
        result[mode] = exact
    return result


def score(directory, revised_format=False):
    controls()
    verifier = revised if revised_format else typed
    rows_out = verifier.verify(directory)
    extract_run = typed.report(rows_out)
    extract_run["prompt"] = verifier.FAMILY
    counts = {"retrospective": Counter(), "fictional": Counter()}
    for key, _, _, source, expected in typed.cards():
        label, span = normalize_vote(rows_out[key], source)
        row = extract_run["readings"][key]
        row["format_compliant"] = row["admitted"] != "unknown" or (
            rows_out[key]["ended"] and rows_out[key]["output"].casefold() == "unknown"
        )
        row["normalized"] = label
        row["normalized_span"] = span
        count = counts["fictional" if key.startswith("control/") else "retrospective"]
        count.update({"rows": 1, "correct": label == expected,
                      "false_vote": label != "unknown" and label != expected,
                      "missed_vote": label == "unknown" and expected != "unknown"})
    extract_run["normalized_counts"] = counts
    extract_run["exact_format_count"] = sum(row["format_compliant"] for row in extract_run["readings"].values())
    reviews = read_witness_review(directory, extract_run["readings"])
    extract_run["witness_review"] = reviews
    extract_run["unsupported_admitted_spans"] = sum(row["adequate"] == "no" for row in reviews.values())
    rows, notes, base_reads = input_state()
    grades, banks, relations = {}, {}, {}
    for mode in MODES:
        reads, scoring, bank = intervene(rows, notes, base_reads, extract_run["readings"], mode)
        grades.update(scoring)
        banks.update(bank)
        relations[mode] = reads
    previous = prior.study.chair.load(ARCHIVE / "results.json")
    for mode in ("literal", "verified_only"):
        for key, row in grades.items():
            if key.endswith(f"/{mode}"):
                assert {k: v for k, v in row.items() if k != "review_id"} == {
                    k: v for k, v in previous["grades"][key].items() if k != "review_id"
                }
    scored = policies(banks)
    for inventory, result in scored.items():
        for arm, policy in result.items():
            for mode in ("literal", "verified_only"):
                assert policy["summary"][mode] == previous["routing"][inventory]["policies"][arm]["summary"][mode]
    paths = (Path(__file__), Path(typed.__file__), Path(verifier.__file__), Path(prior.__file__), Path(search.__file__), ARCHIVE / "review.tsv",
             ARCHIVE / "results.json", directory / "transcript.jsonl", directory / "witness-review.tsv",
             directory / "launch.json")
    return {
        "scope": "Retrospective typed vote control on the two exposed meetings. Official facts come from the "
                 "roll calls and apply only to matching vote queries. The extraction arm replaces those supplied "
                 "facts with frozen model replies admitted by exact quote. Non-vote prose is archived. "
                 "Comma admission is a retrospective format diagnostic. Fictional controls are excluded from routing. No model updates.",
        "official_sources": {
            "2634 (2022)": "https://digitallibrary.un.org/record/3975658",
            "2796 (2025)": "https://documents.un.org/api/symbol/access?l=en&s=S%2FPV.10029&t=pdf",
        },
        "official_facts": [{"speaker": actor, "resolution": resolution, "vote": vote}
                           for (actor, resolution), vote in OFFICIAL_VOTES.items()],
        "extraction": extract_run, "receipt_scores": summaries(grades), "relations": relations,
        "routing": scored, "exact_bounds": bounds(banks, previous, scored), "grades": grades, "hashes": {path.name: typed.prior.runner.digest(path) for path in paths},
    }


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("directory", type=Path)
    p.add_argument("--revised-format", action="store_true")
    args = p.parse_args()
    print(json.dumps(score(args.directory, args.revised_format), indent=2))
