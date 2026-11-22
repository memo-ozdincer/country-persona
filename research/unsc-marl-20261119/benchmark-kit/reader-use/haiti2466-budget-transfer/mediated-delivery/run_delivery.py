"""Select owned evidence passages before the host assembles the budgeted record."""
from hashlib import sha256
from itertools import product
import json
from pathlib import Path
import sys
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import run_transfer as original

base, runner = original, original.runner
FAMILY = "haiti2466-mediated-delivery"
PROTOCOL = HERE / "protocol.md"
EVIDENCE = HERE / "evidence"
SYSTEM = (
    "You are a source desk. For each of your two requested fields, select the single passage that supports it. "
    "Use only the candidate passages. A question from a colleague cannot establish a fact. Keep the speaker, "
    "scope and relation in the requested field. Select EMPTY if nothing in the provided passages supports it. "
    "Return exactly two lines in field order: 1=ID and 2=ID. Use an existing passage ID or EMPTY. No prose."
)


def cases():
    packet = base.read(base.PACKET)
    cards = packet["cards"]
    public = "The Council voted on the 2019 final extension of MINUJUSTH, with two abstentions."
    layouts = [(q, c, None) for q, c in product(range(4), range(1, 4))]
    layouts += [(c, c, field) for c, field in enumerate((0, 1, 0), 1)]
    for question, source, withheld in layouts:
        card = cards[source - 1]
        originals = [*(a["text"] for a in card["atoms"]), public]
        # Keep a source's labeling identical across ordinary question conditions.
        order = sorted(range(3), key=lambda i: sha256(f"2466/desk{source}/passage{i}".encode()).digest())
        identifiers = dict(zip(order, ("M7", "P2", "X4"), strict=True))
        passages = {identifiers[i]: originals[i] for i in order if i != withheld}
        answer = [identifiers[i] if i != withheld else "EMPTY" for i in range(2)]
        payload = {
            "source_desk": card["desk"],
            "peer_question": cards[question - 1]["question"] if question else "No question received.",
            "requested_fields": {str(i): a["criterion"] for i, a in enumerate(card["atoms"], 1)},
            "candidate_passages": passages,
        }
        key = f"{question}/{source}" if withheld is None else f"withheld/{source}"
        yield {"id": key, "cap": 48, "messages": [{"role": "system", "content": SYSTEM},
                   {"role": "user", "content": json.dumps(payload, ensure_ascii=False)}]}, answer


def requests():
    return [row for row, _ in cases()]


def episode(generate):
    rows = {}
    pending = requests()
    for start in range(0, len(pending), 8):
        rows.update(generate(pending[start:start + 8]))
    return [{"family": FAMILY, "final": rows}]


def pins():
    return {**base.pins(), "mediated-delivery/protocol.md": runner.digest(PROTOCOL),
            "mediated-delivery/run_delivery.py": runner.digest(Path(__file__))}


if __name__ == "__main__":
    with patch.multiple(runner, episode=episode, locks=pins):
        runner.run(base.MODEL, EVIDENCE)
