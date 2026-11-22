"""Read private ordinal mandates and disclose a whole card under a limited channel."""
import argparse
from contextlib import contextmanager
from hashlib import sha256
from itertools import product
import json
from pathlib import Path
from unittest.mock import patch

import relay_compromise_language as language

HERE = Path(__file__).resolve().parent
MANDATES = {
    "venezuela": (
        (
            "Require explicit host consent. Prefer a staged release with joint coordination above all. A staged release with UN coordination is a second choice. A broad release with joint coordination is a fallback. Reject every other combination.",
            "Require explicit host consent. Prefer a broad release with joint coordination above all. A staged release with UN coordination is a second choice. A staged release with joint coordination is a fallback. Reject every other combination.",
            "Require explicit host consent and focused scope. Host coordination is the strongest choice, and joint coordination is a second choice. Reject all other combinations.",
        ),
        (
            "Require explicit host consent and staged scope. UN coordination is the strongest choice. Joint coordination is a fallback. Reject all other combinations.",
            "Require explicit host consent and staged scope. Joint coordination is the strongest choice. UN coordination is a fallback. Reject all other combinations.",
            "Require explicit host consent and focused scope. Joint coordination is the strongest choice. Host coordination is a second choice. Reject all other combinations.",
        ),
    ),
    "space": (
        (
            "Use the disarmament forum. A staged study is the strongest choice, a focused study is the second choice, and a staged negotiation is a fallback. Reject all other combinations.",
            "Use the disarmament forum. A staged negotiation is the strongest choice, a staged study is the second choice, and a focused study is a fallback. Reject all other combinations.",
            "Limit acceptable measures to broad negotiations. With a review in the disarmament forum is the strongest choice. Without a review in the Council is the second choice. Reject all other combinations.",
        ),
        (
            "Use the disarmament forum. A staged study is the strongest choice, staged negotiation the second choice, and focused study a fallback. Reject all other combinations.",
            "Use the disarmament forum. A focused study is the strongest choice, staged negotiation the second choice, and staged study a fallback. Reject all other combinations.",
            "Limit acceptable measures to broad negotiations. Without a review in the Council is the strongest choice. With a review in the disarmament forum is the second choice. Reject all other combinations.",
        ),
    ),
}


def order(rotation):
    return (0, 1, 2) if rotation == 0 else (2, 0, 1)


def observations():
    for (family, task), source in zip(language.ranked.fixtures().items(), language.ranked.FILES, strict=True):
        dossier = json.loads(source.read_text())
        packages = dossier["options"]
        names = task.actions[:-1]
        assert names == tuple(p["id"] for p in packages)
        for role, identity, rotation in product(range(2), range(3), range(2)):
            choices = []
            for label, index in zip("ABC", order(rotation), strict=True):
                card = task.cards[role][index]
                choices.append(f"{label}. {language.describe(names, card)}.")
            public = "\n".join(f"{p['id']}: " + "; ".join(f"{key}={v}" for key, v in p.items() if key != "id")
                               for p in packages)
            content = "\n".join((f"Fictional {family} workshop. You hold one private mandate.",
                                 "Use the public package descriptions to match your mandate to one complete scorecard.",
                                 "Strongest choice means strongly preferred. Second choice means preferred. Fallback means acceptable. Omitted packages are rejected.",
                                 "Public package descriptions:", public, "Your private mandate:",
                                 MANDATES[family][role][identity], "Possible disclosures:", *choices,
                                 "D. Withhold the card because no match can be established."))
            yield {"observation": (family, role, identity, rotation, False), "legal": (0, 1, 2, 3),
                   "messages": [{"role": "system", "content": "You are a fictional workshop delegate. Read your own mandate and return only the letter of the complete matching disclosure, or D if you cannot establish a match."},
                                {"role": "user", "content": content}]}


def hashes():
    return {**language.hashes(), Path(__file__).name: sha256(Path(__file__).read_bytes()).hexdigest()}


@contextmanager
def inputs():
    scorer = language.scorer
    with language.inputs(), patch.object(scorer, "observations", new=observations), \
         patch.object(scorer, "hashes", new=hashes):
        yield


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("directory", type=Path)
    cli.add_argument("--model", type=Path, required=True)
    args = cli.parse_args()
    with inputs():
        language.scorer.score(args.model, args.directory)
