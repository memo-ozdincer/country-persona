"""Check enacted extension and prospective review as separate legal propositions."""
import argparse
import json
from pathlib import Path
from unittest.mock import patch

import receipt_ack_binding as binding
import receipt_ack_drc_replay as application

HERE = binding.HERE
runner = binding.runner
CONTROL = HERE / "receipt-ack-binding-evidence/results.json"
PREVIOUS = HERE / "receipt-ack-drc-replay.json"
COLOMBIA = HERE.parent / "colombia2023/case.json"
QUESTIONS = (
    "Does this passage state that an existing mandate was actually extended as an operative decision? "
    "An intended review, willingness to consider, or expressly unmade change does not establish this.",
    "Does this passage state that the Council intended, was willing, or planned to consider a possible "
    "later mandate change or extension? A renewal already adopted does not establish this.",
)
ORDERS = {2: ((0, 1), (1, 0)), 4: ((0, 1, 2, 3), (3, 2, 1, 0))}
LABELS = ((True, False), (False, True), (True, True), (False, False))


def cases():
    drc, review = binding.DRC_SPANS[2:]
    collected = binding.previous.load(COLOMBIA)["public"]["OPERATIVE"]
    extension, later = collected.removeprefix("Resolution 2704, operative paragraphs 1 and 2. ").split(". ", 1)
    assert extension.startswith("The Council extended") and later.startswith("It expressed willingness")
    return {
        "drc/expiry": (drc, 0),
        "drc/review": (review, 1),
        "drc/expiry_date_swap": (drc.replace("1 August", "1 July"), 0),
        "drc/review_date_swap": (review.replace("1 July", "1 August"), 1),
        "drc/both": (drc + "; it " + review, 2),
        "drc/no_act": ("The Council received a briefing on the Group of Experts mandate ahead of 1 July 2024.", 3),
        "drc/negated_extension": ("The Council did not extend the Group of Experts mandate. It intended to review it "
                                  "and act on a possible further extension by 1 August 2024.", 1),
        "drc/negated_review": ("The Council extended the Group of Experts mandate to 1 July 2024. "
                               "It expressed no intention to consider any further extension.", 0),
        "colombia/expiry": (extension + ".", 0),
        "colombia/review": ("The Council " + later.removeprefix("It "), 1),
        "colombia/both": (extension + ". " + later, 2),
        "colombia/no_act": ("The Council received a briefing about the Colombian verification mandate, which was discussed in the meeting.", 3),
        "colombia/expiry_paraphrase": ("The existing mandate of the Verification Mission now runs through 31 October 2024 "
                                       "under the Council's adopted decision.", 0),
        "colombia/review_paraphrase": ("The Council remained open to working on a later extension if the parties agree. "
                                        "It adopted no further extension in this clause.", 1),
    }


def prompts():
    for name, (text, _) in cases().items():
        options = ("enacted extension only", "prospective further extension or review only",
                   "both enacted extension and prospective review or extension", "neither")
        question = ("Classify the legal acts established by this passage. " + " ".join(QUESTIONS)
                    + " Choose the option describing which acts are stated.")
        settings = (("joint", question, options), ("enacted", QUESTIONS[0], ("yes", "no")),
                    ("prospective", QUESTIONS[1], ("yes", "no")))
        for axis, task, menu in settings:
            for n, order in enumerate(ORDERS[len(menu)]):
                labels = {key: menu[i] for key, i in zip("ABCD", order)}
                yield binding.previous.row((name, axis, n), task + " Return only the selection letter.",
                                           {"passage": text, "answer_options": labels}, order)


def pins():
    paths = (Path(__file__), COLOMBIA, PREVIOUS, CONTROL,
             *(HERE.parents[1] / p for p in binding.pins()))
    return {str(p.relative_to(HERE.parents[1])): binding.previous.sha256(p.read_bytes()).hexdigest() for p in paths}


def read_output(path):
    with patch.multiple(runner, observations=prompts, hashes=pins):
        return runner.read(path)


def classify(raw):
    output = {}
    for key, (text, expected) in cases().items():
        votes = {axis: binding.previous.pick(raw, (key, axis)) for axis in ("enacted", "prospective", "joint")}
        enacted, prospective = (binding.stable(votes[axis]) for axis in ("enacted", "prospective"))
        separate = LABELS.index((enacted == 0, prospective == 0)) if None not in (enacted, prospective) else None
        output[key] = {"passage": text, "expected": expected, "separate": separate, "joint": binding.stable(votes["joint"]),
                       "votes": votes}
    return output


def replay(outcomes):
    policy = application.game.stored(binding.previous.POLICY)
    compiled = application.terminal_banks()
    original = binding.previous.load(CONTROL)["examples"]["drc"]
    initial = binding.previous.load(PREVIOUS)["split_or_overlap"]
    summaries = {}
    for name, published in initial.items():
        cases = {}
        prior = application.base.roster(name)
        for target in application.base.PAIRS:
            requested = application.PAIR_NAMES[target]
            refs = published[requested]["routing"]
            for method in ("joint", "separate"):
                mapping = {r["field"]: r[method] if r[method] in range(4) else None
                           for r in original if r["kind"] == "received"} | {None: None}
                forecast = application.score(application.distribution(policy, target, prior, "ack", mapping,
                                                                        application.base.CHAIR), target, compiled)
                assert forecast == refs[f"{method}_read"]
                if method == "joint":
                    # Preserve the historical joint reader as a comparator.
                    mapping = {r["field"]: r["separate"] if r["separate"] in range(4) else None
                               for r in original if r["kind"] == "received"} | {None: None}
                for field, legal in ((2, "expiry"), (3, "review")):
                    force = outcomes[f"drc/{legal}"][method]
                    mapping[field] = 2 + force if force in (0, 1) else None
                after = application.score(application.distribution(policy, target, prior, "ack", mapping,
                                                                     application.base.CHAIR), target, compiled)
                cases.setdefault(requested, {})[method] = {"after": after, "decoded_fields": mapping}
        summaries[name] = cases
    return summaries


def run(directory):
    judgements = classify(read_output(directory))
    counts = {family: {method: sum(row[method] == row["expected"] for key, row in judgements.items()
                                    if key.startswith(family + "/"))
                       for method in ("separate", "joint")} for family in ("drc", "colombia")}
    return {"scope": "Exact clauses and authored date, wording and polarity contrasts. "
                     "Colombia is new to this reader test and previously exposed in the project. "
                     "The DRC replay uses measured classifications and the frozen source-clause writer bank. "
                     "All other receipt decisions remain fixed.", "counts": counts,
            "records": judgements, "replay": replay(judgements)}


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("mode", choices=("run", "score"))
    cli.add_argument("directory", type=Path)
    cli.add_argument("--model", type=Path)
    args = cli.parse_args()
    if args.mode == "run":
        with patch.multiple(runner, observations=prompts, hashes=pins):
            runner.score(args.model, args.directory)
    else:
        print(json.dumps(run(args.directory), ensure_ascii=False, indent=2))
