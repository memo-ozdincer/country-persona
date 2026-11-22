"""Evaluate document-local claim checks through the learned evidence router."""
import argparse
from collections import defaultdict
import json
from pathlib import Path
from unittest.mock import patch

import common_ground
import receipt_handovers as delivery

HERE = delivery.HERE
runner = delivery.runner
RELATIONS = ("supports", "contradicts", "unknown")
ACTIONS = ("retain", "revise", "withhold")
VIEWS = ((0, 1, 2), (2, 1, 0))
SIDES = {
    "haiti": (
        ("China welcomed Kenya's willingness to lead.", "The three African members welcomed Kenya's willingness to lead."),
        ("China voted in favour of the authorization.", "The three African members voted in favour of the authorization."),
        ("China confirmed how much funding it would provide.", "The three African members confirmed how much funding they would provide."),
    ),
    "mali": (
        ("France sought an extension of sanctions.", "Russia sought an extension of sanctions."),
        ("France proposed keeping the Panel of Experts in operation.", "Russia proposed keeping the Panel of Experts in operation."),
        ("France said this would be the final extension of sanctions.", "Russia said this would be the final extension of sanctions."),
    ),
}


def inputs():
    packet = common_ground.generate()
    assert packet["keys"] == delivery.load(HERE / "facilitator-key.json")
    assert packet["inputs"] == delivery.load(HERE / "facilitator-inputs.json")
    return packet


def encoded(key, prompt, payload, options):
    for n, order in enumerate(VIEWS):
        yield {"observation": (*key, n), "legal": order, "messages": [
            {"role": "system", "content": prompt + " Return only the option letter."},
            {"role": "user", "content": json.dumps(payload | {
                "options": {letter: options[idx] for letter, idx in zip("ABC", order, strict=True)}}, ensure_ascii=False)},
        ]}


def questions():
    for row in inputs()["inputs"]:
        prompt = ("Decide whether this is documented common ground. Retain only if the supplied passages establish "
                  "the stated position separately for both sides. Revise if a passage contradicts a side of the claim. "
                  "Withhold when the evidence is insufficient and does not contradict it. Do not infer a vote or a commitment from related support.")
        yield from encoded(("direct", row["id"]), prompt,
                           {"proposed_common_ground": row["proposed_sentence"], "documentary_passages": row["sources"]}, ACTIONS)
        if row["id"] % 4 == 3:
            group = (row["id"] // 4) % 3
            for index, ((source_id, card), claim) in enumerate(zip(row["sources"].items(), SIDES[row["docket"]][group], strict=True)):
                instruction = ("Check whether this one official passage establishes the stated position for the specific speaker, "
                               "contradicts it, or leaves it unknown. Do not attribute a claim by a representative to another body "
                               "or convert support for a measure into a recorded vote.")
                yield from encoded(("source", row["id"], index), instruction,
                                   {"one_side_of_claim": claim, "source": source_id, "documentary_passage": card}, RELATIONS)


def hashes():
    paths = (Path(__file__), Path(common_ground.__file__), *(HERE / name for name in ("facilitator-key.json", "facilitator-inputs.json")),
             *(HERE.parents[1] / key for key in delivery.hashes()),
             common_ground.CROSS / "haiti2023/case.json", common_ground.CROSS / "mali/historical-task.json")
    from hashlib import sha256
    return {str(p.resolve().relative_to(HERE.parents[1])): sha256(p.read_bytes()).hexdigest() for p in paths}


def votes(raw, key, labels):
    return [labels[result] if (result := delivery.choose(raw[(*key, n)])) is not None else None for n in range(2)]


def stable(two):
    return two[0] if two[0] == two[1] else None


def compose(relations):
    if "contradicts" in relations:
        return "revise"
    if len(relations) == 2 and all(r == "supports" for r in relations):
        return "retain"
    return "withhold"


def measure(rows, mode):
    by_action = defaultdict(lambda: {"correct": 0, "total": 0})
    panels = defaultdict(list)
    false_retain = 0
    for row in rows:
        want, got = row["expected"], row[mode]
        by_action[want]["total"] += 1
        by_action[want]["correct"] += got == want
        false_retain += got == "retain" and want != "retain"
        panels[row["id"] // 4].append(got == want)
    return {"by_required_action": dict(by_action), "false_retain": false_retain,
            "all_four_views_correct": sum(all(panel) for panel in panels.values()),
            "total_correct": sum(r["correct"] for r in by_action.values())}


def transfer(rows, mode):
    # A routed cast is averaged over the six distinct proposals and weighted by
    # the known distribution of support-statement receipts, not by uniform masks.
    output = {}
    for prior in ("overlap", "split"):
        output[prior] = {}
        for visible in (True, False):
            weights = delivery.exact_receipt_probabilities(prior, visible)
            metrics = defaultdict(float)
            for row in rows:
                true, predicted = row["expected"], row[mode]
                w = weights[row["id"] % 4] / 6
                metrics["decision_accuracy"] += w * (true == predicted)
                metrics["documented_common_ground_released"] += w * (true == predicted == "retain")
                metrics["false_retention"] += w * (predicted == "retain" and true != "retain")
                metrics["correct_revision"] += w * (true == predicted == "revise")
            output[prior]["visible" if visible else "erased"] = dict(metrics)
    return output


def score(directory):
    with patch.multiple(runner, observations=questions, hashes=hashes):
        raw = runner.read(directory)
    packet = inputs()
    sides = {}
    for row, ref in zip(packet["inputs"], packet["keys"], strict=True):
        if row["id"] % 4 == 3:
            sides[row["id"] // 4] = {
                src: {"votes": votes(raw, ("source", row["id"], i), RELATIONS), "expected": ref["source_relations"][src]}
                for i, src in enumerate(row["sources"])
            }
    rows = []
    for row, ref in zip(packet["inputs"], packet["keys"], strict=True):
        direct_votes = votes(raw, ("direct", row["id"]), ACTIONS)
        observed = {sid: stable(sides[row["id"] // 4][sid]["votes"]) for sid in row["sources"]}
        direct = stable(direct_votes) or "withhold"
        result = compose(list(observed.values()))
        assert compose(list(ref["source_relations"].values())) == ref["decision"]
        rows.append({"id": row["id"], "docket": row["docket"], "proposal": row["proposed_sentence"],
                     "expected": ref["decision"], "direct_votes": direct_votes, "direct": direct,
                     "separate_relations": observed, "separate": result, "oracle": ref["decision"],
                     "published_original": row["proposed_sentence"] if result == "retain" else None})
    return {
        "scope": "Frozen model disposition and source-local claim reading. The side statements are authored. "
                 "Replayed output publishes the existing proposed sentence only after supported retain. "
                 "No replacement prose is generated on revise or withhold. Inventories and receipt losses are simulated.",
        "relations": sides, "rows": rows,
        "measured": {mode: measure(rows, mode) for mode in ("direct", "separate", "oracle")},
        "routing": {mode: transfer(rows, mode) for mode in ("direct", "separate", "oracle")},
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("run", "score"))
    parser.add_argument("directory", type=Path)
    parser.add_argument("--model", type=Path)
    args = parser.parse_args()
    if args.mode == "run":
        with patch.multiple(runner, observations=questions, hashes=hashes):
            runner.score(args.model, args.directory)
    else:
        print(json.dumps(score(args.directory), ensure_ascii=False, indent=2))
