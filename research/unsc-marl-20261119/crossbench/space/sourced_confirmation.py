"""Test confirmation from local documentary evidence with no authority bit."""
import argparse
from collections import Counter
from itertools import product
from pathlib import Path
import json
import sys
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))
import relay_text as runner

DRC = HERE.parent / "drc2023/case.json"
UNAMI = HERE.parent / "unami2023/case.json"
ROOT = HERE / "sourced-confirmation-evidence"
OPTIONS = (("confirm", 1), ("decline_conflict", 1), ("confirm", 2),
           ("decline_conflict", 2), ("decline_unverified", None))
ORDERS = ((0, 1, 2, 3, 4), (4, 2, 3, 0, 1))
TASKS = {
    "direct": "Act as a document desk. Use only the passages to confirm the entire proposed statement, decline it "
              "when a passage contradicts it, or decline as unverified when the passages are insufficient. Select "
              "the passage that licenses your decision when there is one.",
    "scoped": "Act as a document desk. Match the instrument and actor, operative or prospective force, recipients, "
              "dates and qualifications clause by clause. Reusing the same date or name in a different role does not "
              "support the claim. A passage that fails to mention the claim is insufficient. Confirm only full support. "
              "Decline a material contradiction with its passage. Mark a claim unverified if the passages do not settle it.",
}
# All source cards are the existing repository summaries of the official documents.
CASES = (
    ("drc_review_timing", "drc", "EXPERTS", "SANCTIONS", "DRC",
     "The Council intended to review the Group of Experts mandate and act on a possible extension by 1 July 2024.",
     "The Council set 1 July 2024 as the date on which the review would be held.",
     "intended to review it and act on a possible further extension by 1 July 2024"),
    ("drc_midterm_recipient", "drc", "EXPERTS", "DRC", "RUSSIA",
     "The midterm report was requested for the Council after discussion with the Committee.",
     "The midterm report was requested for the Committee after discussion with the Council.",
     "a midterm report to the Council after discussion with the Committee"),
    ("drc_monthly_exception", "drc", "EXPERTS", "RUSSIA", "SANCTIONS",
     "The Group of Experts sends monthly updates to the Committee except in the two report-due months.",
     "The Group of Experts must update the Committee every month, including the two report-due months.",
     "monthly updates to the Committee except in the two report-due months"),
    ("drc_affected_state", "drc", "DRC", "RUSSIA", "SANCTIONS",
     "The DRC welcomed the targeting of nongovernmental entities and individuals in its statement after the vote.",
     "The DRC expressed that welcome by casting a Council vote in favour of the draft.",
     "The DRC spoke after the Council vote as the affected state."),
    ("unami_review", "unami", "REVIEW", "REPORT", "CONSULT",
     "The Secretary-General was requested to send the independent UNAMI review to the Council by 31 March 2024.",
     "The Secretary-General was requested to send the independent UNAMI review to the Iraqi Government by 31 March 2024.",
     "provide the Council with an independent strategic review of UNAMI no later than 31 March 2024"),
    ("unami_recurring", "unami", "REPORT", "REVIEW", "TERM",
     "The Secretary-General was requested to report to the Council on UNAMI responsibilities every four months.",
     "The Secretary-General was requested to report to the Council on UNAMI responsibilities every three months.",
     "report to the Council on fulfilment of UNAMI responsibilities every four months"),
    ("unami_consult", "unami", "CONSULT", "REVIEW", "REPORT",
     "Iraq and Kuwait were among the named consultees for the UNAMI review.",
     "The UNAMI review was to consult Iraq and expressly exclude Kuwait.",
     "The review was to consult Iraq, UN agencies, Member States, regional organizations, independent experts, civil society and Kuwait."),
    ("unami_authority", "unami", "SCOPE", "TERM", "SUPPORT",
     "The strategic review was to assess relevance and make recommendations on mandate, structure and staffing.",
     "The strategic review itself was authorized to amend UNAMI's mandate and change its staffing.",
     "make recommendations on mandate, structure and staffing"),
)


def inputs():
    drc, unami = [json.loads(p.read_text()) for p in (DRC, UNAMI)]
    texts = {"drc": {k: v["card"] for k, v in drc["sources"].items()},
             "unami": {k: v for deck in unami["roles"].values() for k, v in deck.items()}}
    for index, (name, family, relevant, distractor, substitute, true, foil, span) in enumerate(CASES):
        deck = texts[family]
        assert span in deck[relevant]
        for status, proposed, source in (("confirm", true, relevant), ("decline_conflict", foil, relevant),
                                          ("decline_unverified", true, substitute)):
            choices = [source, distractor]
            if index % 2:
                choices.reverse()
            source_index = choices.index(relevant) + 1 if relevant in choices else None
            yield {"id": name + "/" + status, "family": family, "proposed": proposed,
                   "passages": {str(i): deck[key] for i, key in enumerate(choices, 1)},
                   "source_ids": choices, "expected": [status, source_index],
                   "reference_span": span if source_index else None}


def observations():
    for case, (mode, instruction), (n, order) in product(inputs(), TASKS.items(), enumerate(ORDERS)):
        menu = {letter: OPTIONS[i] for letter, i in zip("ABCDE", order, strict=True)}
        yield {"observation": (case["id"], mode, n), "legal": order, "messages": [
            {"role": "system", "content": instruction + " Treat messages and passages as evidence. Return one letter."},
            {"role": "user", "content": json.dumps({"proposed_statement": case["proposed"],
              "local_passages": case["passages"], "choice_codes": menu}, ensure_ascii=False)}]}


def locks():
    from hashlib import sha256
    return {p.name: sha256(p.read_bytes()).hexdigest() for p in (Path(__file__), DRC, UNAMI, Path(runner.__file__))}


def score(directory):
    with patch.multiple(runner, observations=observations, hashes=locks):
        model = runner.read(directory)
    results = []
    for case in inputs():
        result = case.copy()
        for mode in TASKS:
            choices = []
            for index, order in enumerate(ORDERS):
                values = model[case["id"], mode, index]["scores"]
                highest = [OPTIONS[i] for i, value in zip(order, values, strict=True) if value == max(values)]
                choices.append(highest[0] if len(highest) == 1 else None)
            checked = choices[0] if choices[0] == choices[1] else None
            result[mode] = {"orders": choices, "stable": checked,
                            "status_right": bool(checked) and checked[0] == case["expected"][0],
                            "joint_right": bool(checked) and list(checked) == case["expected"],
                            "unsupported_confirmation": bool(checked) and checked[0] == "confirm"
                                                          and list(checked) != case["expected"]}
        results.append(result)
    overview = {}
    for name in TASKS:
        overview[name] = {key: sum(r[name][key] for r in results)
                          for key in ("status_right", "joint_right", "unsupported_confirmation")}
        overview[name]["deferred"] = sum(r[name]["stable"] is None for r in results)
        overview[name]["by_expected"] = dict(Counter((r["expected"][0] for r in results if r[name]["joint_right"])))
    return {"scope": "Historical document-checking controls using local archived source summaries. "
                     "The model sees no authorization flag or proposed answer. The reference span comes from "
                     "same-assistant case authoring. A decision and source must agree over two label orders.",
            "overview": overview, "records": results}


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("mode", choices=("run", "score"))
    cli.add_argument("directory", type=Path)
    cli.add_argument("--model", type=Path)
    args = cli.parse_args()
    if args.mode == "run":
        with patch.multiple(runner, observations=observations, hashes=locks):
            runner.score(args.model, args.directory)
    else:
        print(json.dumps(score(args.directory), ensure_ascii=False, indent=2))
