"""Check explicit dated vote statements against the trusted Outer Space ledger."""
import argparse
import json
from pathlib import Path
import re

import space_atomic_guard as atomic
import space_transfer_episode as study
import space_transfer_judge as judge

DATE = r"(\d{1,2}) ([A-Za-z]+)(?: (\d{4}))?"
SYMBOL = r"(S/\d{4}/\d+)"
LEDGER_VOTE = re.compile(rf"^{DATE}: .+? {SYMBOL}\b")
RECORD_VOTE = re.compile(
    rf"^On {DATE},\s+the (?:Security )?Council (?:then )?voted (?:first )?on {SYMBOL}\b",
    re.IGNORECASE,
)


def votes(ledger):
    by_symbol = {}
    for number, text in ledger.items():
        match = LEDGER_VOTE.match(text)
        if match:
            day, month, year, symbol = match.groups()
            assert year is not None and symbol not in by_symbol
            by_symbol[symbol] = (int(day), month.casefold(), year, number)
    return by_symbol


def audit(answer, ledger):
    by_symbol = votes(ledger)
    examined, errors = [], []
    for index, text in judge.sentence_rows(answer).items():
        match = RECORD_VOTE.match(text)
        if match is None:
            continue
        day, month, year, symbol = match.groups()
        known = by_symbol.get(symbol.upper())
        if known is None:
            continue
        actual = (int(day), month.casefold(), year)
        expected = known[:3]
        record = {"sentence_id": index, "candidate_span": text, "ledger_id": known[3],
                  "ledger_span": ledger[known[3]], "consistent": actual[:2] == expected[:2] and
                  (year is None or year == expected[2])}
        examined.append(record)
        if not record["consistent"]:
            errors.append(record)
    return {"checked": examined, "date_conflicts": errors}


def report(directory, policy):
    blind = judge.cases(directory, policy)
    cases = {key: {"labels": row["labels"], **audit(row["answer"], atomic.LEDGER)}
             for key, row in blind.items()}
    errors = {label for row in cases.values() if row["date_conflicts"] for label in row["labels"]}
    actual_wrong_date = {label for label, target in atomic.TRUTH.items() if target == ("F", 5, 2)}
    assert errors == actual_wrong_date
    # A narrower date check must not claim it evaluated fabricated authorization.
    assert not audit("With majority support, the Council authorized follow-on negotiations.",
                     atomic.LEDGER)["checked"]
    return {"scope": "Exact check of leading day-month vote statements for known instruments. "
                     "A record with no matched statement has no date verdict for that vote.",
            "scorer_sha256": study.runner.digest(Path(__file__)), "cases": cases}


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--policy", type=Path, default=study.OUT / "space-final-routing-policy.json")
    p.add_argument("--generation", type=Path, default=study.OUT / study.NAME)
    options = p.parse_args()
    print(json.dumps(report(options.generation, options.policy), indent=2, ensure_ascii=False))
