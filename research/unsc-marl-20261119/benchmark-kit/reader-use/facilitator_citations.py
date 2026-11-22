"""Attach only evidence-linked citations to a fixed facilitator draft."""
import argparse
import json
from pathlib import Path
from unittest.mock import patch

import facilitator_replacement_score as scored

study = scored.study
HERE = study.HERE
reader = study.prior
runner = reader.runner
PARENT = HERE / "facilitator-replacement-evidence"


def fixtures():
    replacement = reader.delivery.load(PARENT / "results.json")["arms"]["staged"]
    review = reader.delivery.load(PARENT / "annotations.json")["rows"]
    items = reader.inputs()
    for source, gold, record in zip(items["inputs"], items["keys"], replacement["records"], strict=True):
        assert record["id"] == source["id"] and record["proposed"] == source["proposed_sentence"]
        label = review[f"{source['id']:02}/staged"]
        required = scored.required(gold) | set(label.get("additional_citations_needed", []))
        assert required <= source["sources"].keys()
        # Missing necessary prose cannot be recovered by adding citations.
        yield source, record, required


def prompts():
    instruction = ("Is this official card suitable as a citation for at least one specific factual attribution "
                   "actually made in the facilitator's brief? Check that the card supports the stated actor, status "
                   "and material scope. A topic match is insufficient. A card may support one side of an explicitly "
                   "two-sided statement. Do not cite a card merely because another speaker's position is absent from it, "
                   "or because it was among the materials provided.")
    for case, record, _ in fixtures():
        for card, text in case["sources"].items():
            yield from reader.encoded(("citation", case["id"], card), instruction,
                                      {"brief": record["brief"], "source_id": card, "supplied_source": text},
                                      ("cite_for_supported_attribution", "no_suitable_attribution", "contradicts_attribution"))


def pins():
    from hashlib import sha256
    paths = (Path(__file__), Path(scored.__file__), Path(runner.__file__),
             *(PARENT / p for p in ("results.json", "annotations.json", "complete.json", "transcript.jsonl")),
             *(HERE.parents[1] / p for p in reader.hashes()))
    return {str(p.resolve().relative_to(HERE.parents[1])): sha256(p.read_bytes()).hexdigest() for p in paths}


def check(draft, expected, received, chosen):
    prior = set(draft["ids"])
    assert chosen <= received
    appended = sorted(chosen - prior)
    result = draft["brief"] + "".join(f" [{card}]" for card in appended)
    citation_set = prior | chosen
    certified = (draft["format_ok"] and draft["disposition_right"] and draft["source_clear"]
                 and draft["limits_clear"] and set(draft["known_sides_required"]) <= draft["known_sides_preserved"].keys()
                 and citation_set == expected and len(result.split()) <= 48)
    assert result.startswith(draft["brief"])
    return {"brief": result, "added": appended, "excess": sorted(citation_set - expected),
            "missing": sorted(expected - citation_set), "strict": certified}


def summary(rows, method):
    outcome = {}
    for roster in ("overlap", "split"):
        outcome[roster] = {}
        for visible in (True, False):
            masks = reader.delivery.exact_receipt_probabilities(roster, visible)
            stats = {}
            for name in ("retain", "revise", "withhold"):
                stats[name] = sum(masks[r["id"] % 4] / 6 for r in rows if
                                  r["expected_disposition"] == name and r["arms"][method]["strict"])
            outcome[roster]["visible" if visible else "erased"] = stats | {"usable": sum(stats.values())}
    return {"usable": sum(row["arms"][method]["strict"] for row in rows),
            "new_briefs_with_excess_citations": sum(bool(set(row["arms"][method]["excess"]) -
                                                          set(row["arms"]["original"]["excess"])) for row in rows),
            "eligible_revisions": sum(row["expected_disposition"] == "revise" and row["arms"][method]["strict"] for row in rows),
            "eligible_retains": sum(row["expected_disposition"] == "retain" and row["arms"][method]["strict"] for row in rows),
            "replay": outcome}


def score(directory):
    with patch.multiple(runner, observations=prompts, hashes=pins):
        raw = runner.read(directory)
    rows = []
    for case, record, required in fixtures():
        labels = {sid: reader.votes(raw, ("citation", case["id"], sid), ("cite", "no", "conflict"))
                  for sid in case["sources"]}
        suitable = {sid for sid, decision in labels.items() if decision == ["cite", "cite"]}
        visible = set(case["sources"])
        variants = {"original": set(), "frozen_source_reader": suitable, "attach_all_received": visible,
                    "reviewed_oracle": required}
        judged = {method: check(record, required, visible, chosen) for method, chosen in variants.items()}
        assert judged["original"]["strict"] == record["strict"]
        rows.append({"id": case["id"], "expected_disposition": record["expected"], "required_ids": sorted(required),
                     "visible": sorted(visible), "source_decisions": labels, "arms": judged})
    return {"scope": "Post-hoc citation attachment without rewriting or deleting a generated claim. "
                     "The reference citation sets are derived from the same-assistant review. "
                     "The source classifier evaluates local relevance and the strict score separately inherits reviewed prose accuracy. "
                     "The attachment rule does not by itself certify the whole brief.",
            "rows": rows, "summary": {method: summary(rows, method) for method in rows[0]["arms"]}}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("run", "score"))
    parser.add_argument("directory", type=Path)
    parser.add_argument("--model", type=Path)
    args = parser.parse_args()
    if args.mode == "run":
        with patch.multiple(runner, observations=prompts, hashes=pins):
            runner.score(args.model, args.directory)
    else:
        print(json.dumps(score(args.directory), indent=2))
