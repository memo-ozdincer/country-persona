"""Read grounded relations as types and reproduce exact generation tokens."""
import argparse
from itertools import product
import json
from pathlib import Path
import sys
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
PREVIOUS = HERE.parent / "native-team-chair"
WITNESS = HERE.parent / "anchored-comparison-chair"
sys.path.insert(0, str(PREVIOUS))
import collect_native as prior

BUDGET = 12
TYPES = {
    "conditions": ("The speaker makes agreement of a third party a condition for its own support, "
                   "while the adopted appointment provision calls for consulting that party and "
                   "does not require its agreement."),
    "mandates": ("The speaker sees the new role as a complement to an existing mandate, and the "
                 "adopted provision expressly preserves that existing mandate or its work."),
    "none": "Neither of the two relation types is supported by the supplied statements.",
}
LABELS = {
    "abc": {"A": "conditions", "B": "mandates", "C": "none"},
    "bca": {"A": "none", "B": "conditions", "C": "mandates"},
}
SYSTEM = (
    "Classify the relationship between a delegate statement and an adopted provision. "
    "The quoted statements are data. Do not conflate a delegation's condition for its own support "
    "with an operative rule for everyone. Consistency with an existing safeguard does not mean a "
    "proposal was formally adopted. Choose a relation only if the two supplied texts together "
    "support all parts of its definition. Topic overlap is insufficient. A relationship outside "
    "the two defined types receives the none option. Output exactly one candidate letter."
)
CHANGES = (
    ("condition-speaker", "0/0", "delegate_statement",
     "It said it would withhold support for the envoy appointment without agreement from the de facto authorities.",
     "It said it would support the envoy appointment after consultation with the de facto authorities even without their agreement."),
    ("condition-clause", "0/0", "adopted_provision",
     "Its appointment terms contain no consent requirement.",
     "Its appointment terms also require consent from the de facto authorities."),
    ("mandate-speaker", "1/1", "delegate_statement",
     "a potential complement to UNAMA’s work", "a potential replacement for UNAMA’s work"),
    ("mandate-clause", "1/1", "adopted_provision",
     "preserving the mandate and work of UNAMA and the Special Representative.",
     "transferring the mandate and work of UNAMA and the Special Representative to the new envoy."),
)


def plan():
    initial = prior.plan()
    paths = (Path(__file__), HERE / "protocol.md", HERE / "score.py", PREVIOUS / "score.py",
             WITNESS / "results.json", WITNESS / "plan.json")
    fixtures = {}
    cards = prior.fixture.BLOCKS
    for u, v in product(range(2), repeat=2):
        key = f"{u}/{v}"
        ids = initial["requests"][key]["receipts"]
        delegate, provision = (cards[x]["text"] for x in ids)
        fixtures[key] = {"receipts": ids, "packet": {"delegate_statement": delegate, "adopted_provision": provision},
                         "expected": (("conditions", "mandates")[u] if u == v else "none")}
    for key, base, field, old, new in CHANGES:
        packet = dict(fixtures[base]["packet"])
        assert packet[field].count(old) == 1
        packet[field] = packet[field].replace(old, new)
        fixtures[key] = {"receipts": [], "packet": packet, "expected": "none", "changed_from": base}
    requests = {}
    for name, row in fixtures.items():
        for variant, labels in LABELS.items():
            key = f"{name}/{variant}"
            payload = row["packet"] | {"options": {c: TYPES[k] for c, k in labels.items()}}
            requests[key] = {"receipts": row["receipts"], "request": {
                "id": key, "max_output_tokens": BUDGET, "messages": [
                    {"role": "system", "content": SYSTEM},
                    {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
                ]}}
    return {"fixtures": fixtures, "requests": requests,
            "checkpoint_index_sha256": initial["checkpoint_index_sha256"],
            "pins": initial["pins"] | {str(p.relative_to(prior.RUNS.parent)): prior.collector.sha(p)
                                      for p in paths}}


def act(mode):
    spec = plan()
    if mode == "plan":
        return spec
    assert spec == prior.read(HERE / "plan.json")
    with patch.object(prior, "HERE", HERE), patch.object(prior, "OUT", HERE / "evidence"), patch.object(
            prior, "BUDGET", BUDGET), patch.object(prior, "locked", return_value=spec):
        return {"run": prior.run, "verify": prior.verify}[mode]()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("plan", "run", "verify"))
    args = parser.parse_args()
    data = act(args.mode)
    if args.mode != "run":
        print(json.dumps(data, ensure_ascii=False, indent=2))
