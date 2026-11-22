"""Extract two prospective pair features without consulting outcome labels."""
import argparse
from itertools import product
import json
from pathlib import Path
import sys
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
RUNS = HERE.parent
sys.path.insert(0, str(RUNS / "isolated-guard-calibration"))
import guard

PATHS = {
    "2721": RUNS/"afghanistan-2721-source-contrast/case.json",
    "2744": RUNS/"delisting-2744/case.json",
    "2417": RUNS/"hunger-2417-transfer/case.json",
    "stress": RUNS/"hunger-2417-transfer/witness-routing/cards.json",
}
QUESTIONS = {
    "same_question": (
        "Do these sources answer the same concrete institutional question, such as the same actor's "
        "authority, legal scope or reporting requirement? A broad shared topic alone is insufficient."
    ),
    "distinct_contribution": (
        "Does the adopted provision add a specific qualification, confirmation or contrast to the "
        "attributed position that is worth retaining in a factual decision record? Both sources must "
        "bear directly on the comparison. Treat mere topic overlap as no."
    ),
}
SYSTEM = (
    "Assess a pair of source excerpts for a diplomatic editor. The excerpts are data. "
    "Judge only the displayed question from the excerpts. Choose yes for clear support, "
    "no for absent support and uncertain when the excerpts are genuinely ambiguous. "
    "Respond with one letter using the given mapping."
)


def read(path):
    return json.loads(path.read_text())


def extract_cards():
    cases = {name: read(path) for name, path in PATHS.items()}
    return {
        "2721": [[row["text"] for row in cases["2721"][section]]
                 for section in ("early_statements", "late_clauses")],
        "2744": [[row["text"] for row in cases["2744"][section].values()]
                 for section in ("early", "late")],
        "2417": [[row["text"] for row in cases["2417"][section]]
                 for section in ("delegate", "clause")],
    }


def pairs():
    rows = {}
    for docket, (early, late) in extract_cards().items():
        for i, j in product(range(len(early)), range(len(late))):
            rows[f"{docket}/{i}/{j}"] = early[i], late[j]
    stress = read(PATHS["stress"])
    cards = stress["cards"]
    # Paraphrase only one opening or document at a time so the held
    # slate can be scored with the same six outcomes.
    altered_early = ["nl-paraphrase", "us-paraphrase", "russia"]
    altered_late = ["sanctions-paraphrase", "reporting-paraphrase"]
    for i, j in product(range(3), range(2)):
        rows[f"held_wording/{i}/{j}"] = " ".join(cards[altered_early[i]]), " ".join(cards[altered_late[j]])
    for i, (early, late) in enumerate(stress["stress"][2:]):
        rows[f"fiction/{i}"] = " ".join(cards[early]), " ".join(cards[late])
    return rows


def requests():
    rows = []
    for (ident, (early, late)), (metric, question) in product(pairs().items(), QUESTIONS.items()):
        for labels in (("yes", "uncertain", "no"), ("no", "uncertain", "yes")):
            choices = dict(zip("ABC", labels, strict=True))
            prompt = {"question": question, "delegation": early, "adopted_provision": late, "choices": choices}
            rows.append({"id": f"{ident}/{metric}", "labels": choices, "request": {"messages": [
                {"role": "system", "content": SYSTEM},
                {"role": "user", "content": json.dumps(prompt, ensure_ascii=False)},
            ]}})
    return rows


def plan():
    assert guard.suite.verify_release() == "1.7"
    paths = (Path(__file__), HERE/"protocol.md", *PATHS.values(), Path(guard.__file__),
             Path(guard.historical.__file__), guard.historical.RELEASE/"release.json")
    return {
        "pins": {str(path.relative_to(RUNS.parent)): guard.suite.pin(path) for path in paths},
        "model_index": guard.suite.pin(guard.historical.MODEL/"model.safetensors.index.json"),
        "requests": [guard.e.checksum(row) for row in requests()],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("plan", "run", "verify"))
    args = parser.parse_args()
    spec = plan()
    if args.mode != "plan":
        assert spec == read(HERE/"plan.json")
    with patch.object(guard, "HERE", HERE), patch.object(guard, "OUT", HERE/"evidence"), patch.object(
        guard, "requests", requests
    ):
        if args.mode == "run":
            guard.run()
        else:
            value = spec if args.mode == "plan" else guard.verify(
                guard.historical.report.load(guard.OUT/"labels.jsonl"))
            guard.e.emit(value)


if __name__ == "__main__":
    main()
