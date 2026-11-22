"""Probe two decisive evidence clauses on the frozen DPRK passage set."""
import argparse
from hashlib import sha256
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / "benchmark-kit/evidence/duplicate-card-routes"
SEMANTIC_LOCK = EVIDENCE / "semantic-lock.json"
CLAUSES = {
    1: "Does the passage explicitly say Yamazaki spoke in his national capacity as Japan's representative?",
    2: "Does the passage explicitly say China cited remaining time for consultations in explaining its abstention?",
}
ORDERS = ((0, 1), (1, 0))
SYSTEM = (
    "Check the text of one excerpt. Answer Yes only if the passage supports exactly what the question asks. "
    "Answer No if that fact is omitted, contradicted or attributable to a different actor. "
    "A fact can be supported anywhere in the passage, regardless of sentence order. "
    "Use the passage alone and return only the choice letter."
)


def entries():
    return [entry for entry in json.loads(SEMANTIC_LOCK.read_text())["key"] if entry[0] == "dprk"]


def observations():
    for _, source, variant, passage, _ in entries():
        for clause, question in CLAUSES.items():
            for index, order in enumerate(ORDERS):
                prompt = {"passage": passage, "question": question,
                          "choices": {letter: ("Yes" if answer else "No")
                                      for letter, answer in zip("AB", order, strict=True)}}
                yield {"observation": (source, variant, clause, index), "legal": order,
                       "messages": [{"role": "system", "content": SYSTEM},
                                    {"role": "user", "content": json.dumps(prompt, ensure_ascii=False)}]}


def hashes():
    files = (Path(__file__).resolve(), ROOT / "relay_text.py", SEMANTIC_LOCK)
    return {str(path.relative_to(ROOT)): sha256(path.read_bytes()).hexdigest() for path in files}


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
