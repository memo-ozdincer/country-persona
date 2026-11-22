"""Render a verified workshop report from public decks and trusted receipts."""
import argparse
from collections import Counter
from functools import cache
from itertools import product
import json
from pathlib import Path
import re

HERE = Path(__file__).resolve().parent
WORKSPACE = HERE.parents[2]
SPACE = WORKSPACE / "crossbench/space"
REGISTRY = SPACE / "evidence/three-seat-positive.json"
SOURCES = {
    "space": ("apr-amendment", "apr-final"),
    "mali": ("status-638", "status-639"),
    "myanmar": ("vote", "mandate"),
}
SCOPE = "This fictional workshop creates no official action or commitment."
RULE = "Any zero excludes its package. Maximize the minimum grade, then the sum."
WORD_CAP = 165
ROLES = ("First", "Second")


@cache
def history(family):
    ids = SOURCES[family]
    source = WORKSPACE / "crossbench" / family / "historical-task.json"
    blocks = {row["id"]: row["text"] for row in json.loads(source.read_text())["evidence"]}
    return tuple((key, blocks[key]) for key in ids)


def normalize(packages, decks, receipts):
    if len(receipts) != len(ROLES):
        raise ValueError("Expected two role-bound receipt slots")
    terms = []
    for deck, entry in zip(decks, receipts, strict=True):
        if entry is None:
            terms.append(None)
            continue
        if not isinstance(entry, (list, tuple)) or len(entry) != 2:
            raise ValueError("Invalid receipt")
        label, grade = entry
        if label not in packages or type(grade) is not int or not 0 <= grade <= 3:
            raise ValueError("Invalid package or grade")
        column = packages.index(label)
        if not any(card[column] == grade for card in deck):
            raise ValueError("Grade is absent from this role's authorized card deck")
        terms.append((column, grade))
    return terms


def summarize(grid, receipts):
    """Use the same exact proof rule as the tested multi-agent policy."""
    accepted, warrant = grid.information(tuple(normalize(grid.packages, grid.cards, receipts)))
    counts = Counter(tuple(sorted(grid.winners(world))) for world in accepted)
    return len(accepted), tuple(sorted(warrant)), counts


def render(grid, family, receipts):
    witness_count, common, outcomes = summarize(grid, receipts)
    checked = common[0] if common else "unresolved"
    if not common:
        packed = ", ".join(f"{'/'.join(labels)}×{n}" for labels, n in sorted(outcomes.items()))
        conclusion = f"Outcome sets: {packed}. No common disposition."
    elif checked == "impasse":
        conclusion = "Every package has a zero in every compatible completion, so impasse is warranted."
    else:
        conclusion = f"Package {checked} is among the winners in every compatible completion."
    reported = " ".join(
        f"{role} desk reported {r[0]}={r[1]}." if r is not None else f"{role} desk's report is unavailable."
        for role, r in zip(ROLES, receipts, strict=True)
    )
    clauses = [
        f"Workshop disposition: {checked}",
        " ".join(text for _, text in history(family)),
        SCOPE,
        f"{reported} {RULE} Compatible completions: {witness_count}. {conclusion}",
    ]
    text = "\n\n".join(clauses)
    if len(text.split()) > WORD_CAP:
        raise ValueError("Report exceeds the word cap")
    return text


def independent_outcomes(grid, receipts):
    if len(receipts) != 2:
        raise ValueError("Expected two receipt slots")
    compatible = []
    for a, b in product(*grid.cards):
        if any(r is not None and dict(zip(grid.packages, card, strict=True)).get(r[0]) != r[1]
               for card, r in zip((a, b), receipts, strict=True)):
            continue
        scores = []
        for label, votes in zip(grid.packages, zip(a, b, grid.public, strict=True), strict=True):
            if all(votes):
                scores.append((min(votes), sum(votes), label))
        if scores:
            best = max((minimum, total) for minimum, total, _ in scores)
            compatible.append(tuple(sorted(label for minimum, total, label in scores if (minimum, total) == best)))
        else:
            compatible.append(("impasse",))
    if not compatible:
        raise ValueError("No compatible completion")
    common = set(compatible[0]).intersection(*compatible[1:])
    return compatible, common


def verify(grid, family, receipts, report):
    """Parse the actual report and independently check each displayed fact."""
    normalize(grid.packages, grid.cards, receipts)
    compatible, common = independent_outcomes(grid, receipts)
    header, archive, boundary, body = report.split("\n\n")
    heading = re.fullmatch(r"Workshop disposition: ([A-Z]|impasse|unresolved)", header)
    if not heading or heading[1] not in (common or {"unresolved"}):
        raise ValueError("Wrong disposition")
    if archive != " ".join(text for _, text in history(family)) or boundary != SCOPE:
        raise ValueError("Wrong official history or scope")
    lead, separator, tail = body.partition(f" {RULE} ")
    if not separator:
        raise ValueError("Missing or altered ranking rule")
    reports = re.fullmatch(
        r"(?:First desk reported ([A-Z])=([0-3])\.|First desk's report is unavailable\.) "
        r"(?:Second desk reported ([A-Z])=([0-3])\.|Second desk's report is unavailable\.)", lead
    )
    if reports is None:
        raise ValueError("Wrong role formatting")
    matches = [None if reports[i] is None else [reports[i], int(reports[i+1])] for i in (1,3)]
    if matches != [list(r) if r is not None else None for r in receipts]:
        raise ValueError("Wrong grade or authorship")
    rest = re.fullmatch(r"Compatible completions: ([1-9][0-9]*)\. (.+)", tail)
    if not rest or int(rest[1]) != len(compatible):
        raise ValueError("Wrong completion count")
    conclusion = rest[2]
    if not common:
        summary = re.fullmatch(r"Outcome sets: (.+)\. No common disposition\.", conclusion)
        if not summary:
            raise ValueError("Wrong unresolved reasoning")
        claimed = Counter()
        for row in summary[1].split(", "):
            match = re.fullmatch(r"([A-Z](?:/[A-Z])*|impasse)×([1-9][0-9]*)", row)
            if not match:
                raise ValueError("Malformed completion outcome")
            outcome_set = tuple(match[1].split("/"))
            if outcome_set in claimed:
                raise ValueError("Duplicate completion counts")
            claimed[outcome_set] = int(match[2])
        if claimed != Counter(compatible):
            raise ValueError("Wrong unresolved outcome sets")
    elif heading[1] == "impasse":
        if conclusion != "Every package has a zero in every compatible completion, so impasse is warranted.":
            raise ValueError("Wrong impasse reasoning")
    else:
        stated = re.fullmatch(r"Package ([A-Z]) is among the winners in every compatible completion\.", conclusion)
        if not stated or stated[1] != heading[1]:
            raise ValueError("Wrong package or tie statement")
    words = len(report.split())
    if words > WORD_CAP:
        raise ValueError("Report exceeds the word cap")
    return dict(disposition=heading[1], completions=len(compatible), words=words, release_points=70,
                settled_points=70 if common else 0)


def cli():
    import sys
    from unittest.mock import patch

    sys.path.insert(0, str(SPACE))
    import three_seat_transfer as shared
    import three_seat_positive_fit as fit

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("grid", choices=("196", "198", "199", "217", "mali", "myanmar"))
    parser.add_argument("receipts", help='Trusted JSON receipt array, such as [["A",0],null]')
    opts = parser.parse_args()
    if opts.grid in ("mali", "myanmar"):
        grid, family = shared.Grid(opts.grid), opts.grid
    else:
        registry = json.loads(REGISTRY.read_text())
        assert int(opts.grid) in registry["partition"]["reserved"]
        fixture, = (fit.fixture(row) for row in registry["accepted"] if row["draw"] == int(opts.grid))
        with patch.dict(shared.FIXTURES, {"render": fixture}):
            grid, family = shared.Grid("render"), "space"
    receipts = json.loads(opts.receipts)
    text = render(grid, family, receipts)
    verify(grid, family, receipts, text)
    print(text)


if __name__ == "__main__":
    cli()
