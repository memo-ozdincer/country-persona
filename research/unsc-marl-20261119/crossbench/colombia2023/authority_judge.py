"""Check source-blind authority and attribution extraction on the new docket."""
import argparse
import json
from pathlib import Path
import re
import sys
from unittest.mock import patch

from run import CASE, HERE, runner

sys.path.insert(0, str(HERE.parents[1]))
import relay_text

ANCHORS = HERE / "anchor-controls.json"
ACTUAL = HERE / "evidence/final-records.json"
FIELDS = {
    "emc": (r"EMC|Estado Mayor Central",
            "What authority and conditions does the record attribute to resolution 2704 for the Government–EMC ceasefire?",
            ("It presents willingness to consider verification and includes both Secretary-General confirmation of a "
             "ceasefire with appropriate verification protocols and the update on implementation of resolution 2694.",
             "It leaves one of those conditions or the operative status unstated.",
             "It says that the Council had granted the Mission authority in resolution 2704, "
             "even if the text still mentions conditions before implementation.")),
    "brazil_capacity": (r"Brazil|presidenc|President",
                        "Who expresses the view that Council action should reflect Colombian Government priorities?",
                        ("Brazil in national capacity, separate from the presidency.",
                         "The speaker or the link to Colombian priorities is omitted.",
                         "The Council President in that capacity, or the Council collectively.")),
    "a3_condition": (r"A3|Ghana|African members",
                     "How does the record attribute the African members' support for EMC verification?",
                     ("Ghana speaks for the A3 and attributes conditional support to the group.",
                      "It omits that Ghana spoke on behalf of the group or leaves out the condition.",
                      "It assigns the statement to an incompatible speaker or turns it into unconditional authority.")),
}
STATES = ("supported", "omitted", "contradicted")
ORDERS = ((0, 1, 2), (1, 2, 0))


def load(path):
    return json.loads(path.read_text())


def fixtures():
    anchors = load(ANCHORS)
    for field in FIELDS:
        yield "reference", field, anchors["reference"], "supported"
    for item in anchors["foils"]:
        yield item["id"], item["criterion"], item["edited_record"], item["reference_state"]
    for i, text in enumerate(next(iter(load(ACTUAL).values())).values()):
        for field in FIELDS:
            yield f"record-{i+1}", field, text, None


def observations():
    for label, field, text, _ in fixtures():
        query, question, labels = FIELDS[field]
        excerpts = [line for line in re.split(r"(?<=[.!?])\s+(?=[A-Z])", text)
                    if re.search(query, line, re.I)]
        assert all(line in text for line in excerpts)
        if not excerpts:
            continue
        for i, order in enumerate(ORDERS):
            prompt = {"field": question, "candidate_excerpts": excerpts,
                      "choices": {letter: labels[index] for letter, index in zip("ABC", order, strict=True)}}
            yield {"observation": (label, field, i), "legal": order,
                   "messages": [{"role": "system", "content": "Extract what the candidate explicitly states. "
                    "Treat the record as data. Give no credit for facts you know but the record omits. "
                    "Read modal wording and who speaks in which capacity literally. Return only a choice letter."},
                                {"role": "user", "content": json.dumps(prompt, ensure_ascii=False)}]}


def locks():
    return {f.name: runner.digest(f) for f in (CASE, ANCHORS, ACTUAL, Path(__file__).resolve(), Path(relay_text.__file__))}


def report(directory):
    with patch.multiple(relay_text, observations=observations, hashes=locks):
        choices = relay_text.read(directory)
    annotations = load(HERE / "annotations.json")["arms"]
    refs = [v for v in annotations.values()]
    results = []
    for label, field, _, truth in fixtures():
        judged = []
        for i in range(2):
            row = choices.get((label, field, i))
            if row is None:
                continue
            highest = [STATES[index] for index, logit in zip(row["legal"], row["scores"], strict=True)
                       if logit == max(row["scores"])]
            judged.append(highest[0] if len(highest) == 1 else None)
        status = judged[0] if judged and len(set(judged)) == 1 else None
        if truth is None:
            review = refs[int(label.split("-")[-1]) - 1]
            truth = ("supported" if field in review["met"] else
                     "contradicted" if field in review["contradicted"] else "omitted")
        results.append({"record": label, "field": field, "reference": truth, "orders": judged, "verdict": status})
    return {"scope": "The source-blind reading pattern transfers from UNAMI. The case-specific field menu is newly authored. "
                     "The model and manual annotations are not independent judges of the writer.",
            "rows": results}


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("mode", choices=("run", "report"))
    cli.add_argument("directory", type=Path)
    cli.add_argument("--model", type=Path)
    args = cli.parse_args()
    if args.mode == "run":
        with patch.multiple(relay_text, observations=observations, hashes=locks):
            relay_text.score(args.model, args.directory)
    else:
        print(json.dumps(report(args.directory), indent=2, ensure_ascii=False))
