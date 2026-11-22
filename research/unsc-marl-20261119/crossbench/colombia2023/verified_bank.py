"""Build a source-linked positive-control record for each received source set."""
from itertools import combinations
import json
import re

from run import CASE, HERE, runner

ANCHORS = HERE / "anchor-controls.json"
ACCESSION = HERE / "accession.json"
PARTIES = re.compile(r"\[([A-Z0-9, ]+)\]")


def compile_bank():
    case = json.loads(CASE.read_text())
    accession = json.loads(ACCESSION.read_text())
    reference = json.loads(ANCHORS.read_text())["reference"]
    assert accession["case_sha256"] == runner.digest(CASE)
    public, cards, derived = [], {}, []
    seen = set()
    cursor = 0
    for match in PARTIES.finditer(reference):
        dependencies = frozenset(k.strip() for k in match.group(1).split(","))
        text = reference[cursor:match.end()].strip()
        assert text and dependencies not in seen
        seen.add(dependencies)
        if dependencies == {"VOTE"}:
            public.append(text)
        elif len(dependencies) == 1:
            source, = dependencies
            cards[source] = text
        else:
            derived.append((dependencies, text))
        cursor = match.end()
    assert not reference[cursor:].strip() and list(cards) == ["OPERATIVE", "ADDITIONAL", "BRAZIL", "A3"]
    rules = {key: frozenset(source.strip() for source in value[0].split(","))
             for key, value in case["rules"].items()}
    covered_ids = {"VOTE", *cards}
    assert all(dependencies <= covered_ids for dependencies in rules.values())

    bank = {}
    for size in range(len(cards) + 1):
        for subset in combinations(cards, size):
            available = frozenset({"VOTE", *subset})
            text = " ".join(public + [cards[k] for k in subset] + [line for deps, line in derived if deps <= available])
            pts = {name: sorted(dependencies) for name, dependencies in rules.items() if dependencies <= available}
            cited = {k.strip() for match in PARTIES.finditer(text) for k in match.group(1).split(",")}
            assert cited == available and len(text.split()) <= 185
            bank[frozenset(subset)] = {"record_points": 7 * len(pts), "text": text, "proof": pts}
    assert bank[frozenset(cards)]["record_points"] == 70
    assert all(a["record_points"] <= b["record_points"] for ids_a, a in bank.items()
               for ids_b, b in bank.items() if ids_a < ids_b)
    return tuple(cards), bank


if __name__ == "__main__":
    ids, bank = compile_bank()
    print(json.dumps({"card_order": ids, "records": {",".join(sorted(ids)): row for ids, row in bank.items()}},
                     indent=2, ensure_ascii=False))
