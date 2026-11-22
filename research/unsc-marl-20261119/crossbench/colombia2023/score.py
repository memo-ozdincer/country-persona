"""Recompute record and transcript measures from adjudicated verbatim spans."""
import argparse
import json
from pathlib import Path

from run import CASE, HERE, runner

EVIDENCE = HERE / "evidence"
POINT_ID = {"renewal", "eln", "emc", "brazil_national", "a3"}
ARGUMENT_ID = {"prior_vs_prospective", "confirmation", "brazil_ownership", "a3_conditions", "ethnic_interests"}


def read(path):
    return json.loads(path.read_text())



def final_review(rules, row, review):
    text = row["output"]
    assert review["met"].keys() <= rules.keys()
    assert all(spans and all(span in text for span in spans) for spans in review["met"].values())
    assert all(issue["span"] in text and issue["reason"] for issue in review["guard_issues"])
    points = 7 * len(review["met"])
    words = len(text.split())
    clear = not review["guard_issues"]
    return {"points": points, "word_count": words, "source_guard_clear": clear,
            "complete": row["ended"], "strict": points == 70 and words <= 185 and clear and row["ended"],
            "evidence_spans": {key: {"source_ids": rules[key][0], "final": spans} for key, spans in review["met"].items()},
            "missing_or_contradicted": sorted(rules.keys() - review["met"].keys())}


def run(directory=EVIDENCE, annotations=HERE / "annotations.json"):
    rubric = read(CASE)
    rules = rubric["rules"]
    raw = directory / "transcript.jsonl"
    labels = read(annotations)
    assert labels["transcript_sha256"] == runner.digest(raw)
    turns = {row["id"].split("/", 1)[1]: row for row in map(json.loads, raw.read_text().splitlines())}
    assert len(turns) == 13
    output = {}
    for arm, review in labels["arms"].items():
        lead = arm if arm == "pooled_solo" else "common"
        names = [f"{lead}/opening_{j}" for j in (0, 1)] + [f"{arm}/revision_{j}" for j in (0, 1)]
        end = f"{arm}/chair"
        final = turns[end]
        covered = [{idea for turn, ideas in review["working_ideas"].items() if turn in (names[j], names[j + 2])
                    for idea in ideas} for j in (0, 1)]
        assert set(review["working_ideas"]) == set(names)
        for turn, ideas in review["working_ideas"].items():
            assert all(quote and quote in turns[turn]["output"] for quote in ideas.values())
        arguments = review["arguments"]
        assert arguments.keys() <= ARGUMENT_ID
        for grade, turn, quote in arguments.values():
            assert grade in (1, 2) and turn in names and quote in turns[turn]["output"]
        output[arm] = {**final_review(rules, final, review),
                       "working_turns": len(names), "synthesis_turns": 1,
                       "key_points_of_10": 2 * len(set.union(*covered) & POINT_ID),
                       "arguments_of_10": sum(grade for grade, _, _ in arguments.values()),
                       "argument_witnesses": arguments,
                       "distinct_tracked_ideas_by_working_slot": [len(ideas) for ideas in covered],
                       "input_tokens": sum(len(turns[turn]["input_ids"]) for turn in names + [end]),
                       "output_tokens": sum(len(turns[turn]["output_ids"]) for turn in names + [end]),
                       "cap_hits": [turn for turn in names + [end] if not turns[turn]["ended"]]}
    interaction = []
    for j in (0, 1):
        peer = f"common/opening_{1-j}"
        own = f"common/opening_{j}"
        revise = f"interactive/revision_{j}"
        other = f"independent_drafts/revision_{j}"
        lookup = labels["arms"]["interactive"]["working_ideas"]
        independent = labels["arms"]["independent_drafts"]["working_ideas"]
        assert turns[peer]["id"] in turns[revise]["seen"] and turns[peer]["id"] not in turns[other]["seen"]
        uptake = lookup[revise].keys() & lookup[peer].keys() - lookup[own].keys() - independent[other].keys()
        interaction.append({"peer": peer, "matched_revisions": [other, revise], "tracked_ideas": sorted(uptake),
                            "input_spans": {idea: lookup[peer][idea] for idea in uptake},
                            "output_spans": {idea: lookup[revise][idea] for idea in uptake}})
    graded = labels["interaction_review"]
    supported_opportunities = {(row["peer"], row["matched_revisions"][-1], idea)
                               for row in interaction for idea in row["tracked_ideas"]}
    assert len(graded) <= 5
    assert all((peer, revision, idea) in supported_opportunities and grade in (1, 2)
               for peer, revision, idea, grade in graded)
    output["interactive"]["interactions_of_10"] = sum(row[-1] for row in graded)
    for arm in ("pooled_solo", "independent_drafts"):
        output[arm]["interactions_of_10"] = None
    return {"scope": labels["scope"], "records": output, "peer_specific_recurrence": interaction}


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--evidence", type=Path, default=EVIDENCE)
    cli.add_argument("--annotations", type=Path, default=HERE / "annotations.json")
    args = cli.parse_args()
    print(json.dumps(run(args.evidence, args.annotations), indent=2, ensure_ascii=False))
