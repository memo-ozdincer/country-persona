"""Distinguish the consultation-time reason from reversals and scope decoys."""
import argparse
from hashlib import sha256
import json
from pathlib import Path

from duplicate_card_atomic import ROOT, SEMANTIC_LOCK, entries as archived

CHOICES = (
    "The passage does not give a consultation-time reason for China's abstention.",
    "China said it abstained in part because time for consultations remained.",
    "China said it abstained in part because no time for consultations remained.",
)
ORDERS = ((0, 1, 2), (1, 2, 0), (2, 0, 1))
SYSTEM = (
    "Use only the excerpt. Identify which statement correctly describes the stated reason "
    "for China's abstention. A separate statement about time is not an abstention reason "
    "unless the passage links it to China's explanation. Return one choice letter."
)


def entries():
    for _, source, variant, passage, _ in archived():
        truth = 0
        if source == 2:
            truth = {"full": 1, "reordered": 1, "missing": 0, "reversed": 2}[variant]
        yield source, variant, passage, truth

    _, _, _, incomplete, _ = next(row for row in archived() if row[1:3] == [2, "missing"])
    yield 2, "other_actor", incomplete + " Japan said consultation time remained.", 0
    yield 2, "other_agenda", incomplete + (
        " On a different agenda item, China said consultation time remained."
    ), 0


def observations():
    for source, variant, passage, _ in entries():
        for index, order in enumerate(ORDERS):
            prompt = {"passage": passage, "choices": dict(zip("ABC", (CHOICES[i] for i in order), strict=True))}
            yield {"observation": (source, variant, index), "legal": order,
                   "messages": [{"role": "system", "content": SYSTEM},
                                {"role": "user", "content": json.dumps(prompt, ensure_ascii=False)}]}


def hashes():
    paths = (Path(__file__).resolve(), Path(__file__).with_name("duplicate_card_atomic.py").resolve(),
             ROOT / "relay_text.py", SEMANTIC_LOCK)
    return {str(path.relative_to(ROOT)): sha256(path.read_bytes()).hexdigest() for path in paths}


def run(model, directory):
    import sys
    from unittest.mock import patch

    sys.path.insert(0, str(ROOT))
    import relay_text
    with patch.multiple(relay_text, observations=observations, hashes=hashes):
        relay_text.score(model, directory)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--model", type=Path, required=True)
    args = parser.parse_args()
    run(args.model, args.directory)
