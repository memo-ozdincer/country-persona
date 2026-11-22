"""Test whether a live question selects a useful source under a one-card delivery limit."""
import argparse
import json
from pathlib import Path
from unittest.mock import patch

import facilitator_event_transfer as prior

FAMILY = "facilitator-requested-evidence"
HERE = Path(__file__).resolve().parent
EVIDENCE = HERE / FAMILY
ARMS = ("peer", "independent", "verbatim_query", "solo", "direct_one", "direct_all")
OPEN = "Ask the source desk one concrete question that would help answer the editor. Ask for evidence and leave the factual answer open."
REPLY = (
    "Choose one document card most useful to the chair. Read both cards before choosing. If there is a "
    "peer question, prioritize evidence that answers it. Otherwise choose the most informative card for the "
    "chair's general mandate. Reply with only the capital letter A or B."
)
FINAL = (
    "Write a public Council record of at most 95 words. Identify the actual Council decision, vote tally and "
    "abstaining actor. Give the editorial answer with correct speaker attribution, or state the precise gap "
    "if the delivered sources cannot establish it. Describe what the resolution asks about investigations or "
    "accountability and make the limit of Council action clear. Cite [S0], [S1] and the supplied card IDs "
    "inline where used. Cite only delivered documentary evidence. Working notes are leads, not evidence."
)
GENERAL = "Prepare an accurate account of resolution 2730 and distinguish Council action from member statements."


def packet():
    return json.loads((EVIDENCE / "packet.json").read_text())


def cases():
    source = packet()
    for name, task in source["tasks"].items():
        yield name, task["request"], source["public"], source["decks"][task["deck"]]


def openers():
    for name, request, public, _ in cases():
        yield prior.prompt(f"{name}/opening", 42, OPEN, {"editorial_question": request, "public_sources": public})


def replies(rows):
    for name, request, _, cards in cases():
        common = {"chair_mandate": GENERAL, "document_cards": cards}
        yield prior.prompt(f"{name}/peer/selection", 8, REPLY,
                           common | {"peer_question": rows[f"{name}/opening"]["output"]})
        yield prior.prompt(f"{name}/verbatim_query/selection", 8, REPLY,
                           common | {"peer_question": request})
        yield prior.prompt(f"{name}/solo/selection", 8, REPLY,
                           common | {"peer_question": rows[f"{name}/opening"]["output"], "editorial_question": request})
    for deck, cards in packet()["decks"].items():
        yield prior.prompt(f"{deck}/independent/selection", 8, REPLY,
                           {"chair_mandate": GENERAL, "document_cards": cards})


def selected(row):
    answer = row["output"]
    return answer if row["ended"] and answer in ("A", "B") else None


def receipt(name, arm, rows):
    deck = packet()["tasks"][name]["deck"]
    if arm in ("solo", "direct_all"):
        return ("A", "B")
    if arm == "direct_one":
        return ("A",)
    panel = deck if arm == "independent" else name
    choice = selected(rows[f"{panel}/{arm}/selection"])
    return (choice,) if choice else ()


def finals(rows):
    for name, request, public, cards in cases():
        for arm in ARMS:
            visible = public | {sid: cards[sid] for sid in receipt(name, arm, rows)}
            payload = {"editorial_question": request, "documentary_evidence": visible}
            if arm == "solo":
                payload["working_note"] = {
                    "question": rows[f"{name}/opening"]["output"],
                    "candidate_card": rows[f"{name}/solo/selection"]["output"],
                }
            yield prior.prompt(f"{name}/{arm}/final", 136, FINAL, payload)


def episode(generate):
    rows = generate(list(openers()))
    rows.update(generate(list(replies(rows))))
    outputs = list(finals(rows))
    for beginning in range(0, len(outputs), 10):
        rows.update(generate(outputs[beginning:beginning + 10]))
    return [{"family": FAMILY, "final": rows}]


def pins():
    files = [Path(__file__), Path(prior.__file__), Path(prior.runner.__file__),
             EVIDENCE / "packet.json", EVIDENCE / "rubric.md", EVIDENCE / "provenance.json"]
    return {str(file.relative_to(HERE.parents[1])): prior.runner.digest(file) for file in files}


def verify(directory):
    with patch.multiple(prior, local=openers, audits=replies, syntheses=finals, pins=pins, FAMILY=FAMILY):
        return prior.read(directory)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("run", "verify"))
    parser.add_argument("directory", type=Path)
    parser.add_argument("--model", type=Path)
    args = parser.parse_args()
    if args.mode == "verify":
        print(json.dumps({"verified_generations": len(verify(args.directory))}))
    else:
        with patch.multiple(prior.runner, episode=episode, locks=pins):
            prior.runner.run(args.model, args.directory)
