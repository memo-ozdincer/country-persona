"""Check whether a cited claim and the exact competing assertion can coexist."""
import argparse
from hashlib import sha256
from pathlib import Path
from unittest.mock import patch

import facilitator_quote_order as quote
import facilitator_receipt_ceiling as ceiling

HERE = quote.HERE
runner = quote.runner
base = quote.base
FAMILY = "facilitator-scope-check"
CAP = 84
READS = HERE / "facilitator-witness-evidence/results.json"
NEW = ceiling.EVIDENCE
ALIASES = HERE / "facilitator-receipt-alias-results.json"
TASK = (
    "Check whether the assertion and the cited evidence can both be true of the same named speaker. "
    "Consider what the speaker actually said or did, not a position that seems likely. "
    "Choose conflict only if the cited action, actor, time and scope directly rule out the exact assertion. "
    "A weaker statement, a qualification on a stronger claim, a different act, or silence can leave the assertion open. "
    "If both can be true, give one concrete compatible reading. If they conflict, explain the opposing act or position. "
    "Return one line, starting with open| or conflict|, followed by a short explanation of at most 25 words."
)


def source_cards():
    cards_by_panel = {}
    for panel, _, local, _, _, cards, _, _, _ in quote.prior.typed.prior.source_inputs():
        cards_by_panel[panel] = [(f"{speaker} {local}.", card) for speaker, card in cards]
    for panel, _, local, _, cards in quote.held.panels():
        cards_by_panel[panel] = [(f"{speaker} {local}.", card) for speaker, card in cards]
    for family, number in base.PANELS:
        predicates = base.transfer.PANELS[family][number][1]
        cards = base.transfer.packets()[family]
        cards_by_panel[f"{family}-{number}"] = [(f"{speaker} {predicate}.", card)
                                                for (speaker, card), predicate in zip(cards, predicates, strict=True)]
    return cards_by_panel


def main_cases():
    old = base.load(READS)["reads"]
    latest = base.load(NEW)["all_reads"]
    mapping = source_cards()
    for group, cases in ceiling.datasets().items():
        for (panel, _), case in cases.items():
            family, number = panel.rsplit("-", 1)
            for i, relation in enumerate(case["reads"]):
                if relation != "contradicts":
                    continue
                sid = f"S{i+1}"
                claim, source = mapping[panel][i]
                if group == "unifil_colombia":
                    item = old[f"{family}/{number}/{i}"]
                else:
                    item = latest[f"{panel}/{sid}/direct/relation_first"]
                witness = item["witness"]
                assert item["admitted"] == relation and witness in source
                desired = "conflict" if case["receipts"][frozenset({i})]["expected"] == "revise" else "open"
                yield f"{panel}/{sid}", {"assertion": claim, "cited_words": witness, "official_card": source}, desired


def cases():
    main = {key: (payload, target) for key, payload, target in main_cases()}
    for key, (payload, target) in main.items():
        yield key, payload, target
    variants = (
        ("unifil/full", "unifil-3/S2", "China said the text fully addressed Lebanon's concerns.", "conflict"),
        ("unifil/shortfall", "unifil-3/S2", "China said the text did not fully address Lebanon's concerns.", "open"),
        ("bosnia/closure", "bosnia-1/S2", "Russia called for closing the Office of the High Representative.", "open"),
        ("bosnia/renewal", "bosnia-1/S2", "Russia voted to renew EUFOR-Althea.", "open"),
        ("abyei/abstention", "abyei-1/S2", "Russia abstained on resolution 2760 (2024).", "open"),
        ("abyei/against", "abyei-1/S2", "Russia voted against resolution 2760 (2024).", "conflict"),
        ("minusca/six_months", "central-african-republic-1/S2", "The United States proposed a six-month extension.", "open"),
        ("minusca/conditional", "central-african-republic-1/S2", "The United States was willing to negotiate a twelve-month renewal under certain conditions.", "open"),
        ("colombia/conditions", "colombia-1/S2", "The three African members supported verification contingent on the Secretary-General's conditions.", "open"),
    )
    for tag, original, assertion, target in variants:
        payload, _ = main[original]
        yield f"control/{tag}", payload | {"assertion": assertion}, target


def requests():
    return [quote.held.prompt(key, CAP, TASK, payload) for key, payload, _ in cases()]


def episode(generate):
    records = {}
    wanted = requests()
    for start in range(0, len(wanted), 10):
        records.update(generate(wanted[start:start+10]))
    return [{"family": FAMILY, "final": records}]


def pins():
    paths = (Path(__file__), READS, NEW, ALIASES, Path(ceiling.__file__),
             *(HERE.parents[1] / key for key in quote.pins()))
    return {str(p.resolve().relative_to(HERE.parents[1])): sha256(p.read_bytes()).hexdigest() for p in paths}


def read(directory):
    expected = pins()
    with patch.multiple(base, pins=lambda: expected, requests=requests, CAP=CAP, FAMILY=FAMILY):
        return base.rows(directory)


def parse(row):
    label, delimiter, reason = row["output"].partition("|")
    return label.strip().casefold() if (row["ended"] and delimiter and reason.strip()
                                       and "\n" not in row["output"] and label.strip().casefold() in ("open", "conflict")) else None


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode", choices=("run", "verify"))
    p.add_argument("directory", type=Path)
    p.add_argument("--model", type=Path)
    args = p.parse_args()
    if args.mode == "run":
        with patch.multiple(runner, episode=episode, locks=pins):
            runner.run(args.model, args.directory)
    else:
        print("Verified", len(read(args.directory)), "generations")
