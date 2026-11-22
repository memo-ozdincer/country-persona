"""Put public package terms next to grades in each disclosure choice."""
import argparse
from contextlib import contextmanager
from hashlib import sha256
import json
from pathlib import Path
from unittest.mock import patch

import relay_ranked_mandates as base


def display(package):
    if "explicit_consent" in package:
        approval = "with explicit host consent" if package["explicit_consent"] else "without explicit host consent"
        return f"{package['scope']} scope, {package['coordination'].upper()} coordination, {approval}"
    review = "with a review" if package["review"] else "without a review"
    forum = "the disarmament forum" if package["forum"] == "disarmament" else "the Council"
    return f"{package['scope']} {package['instrument']} in {forum} {review}"


def observations():
    fixtures = base.language.ranked.fixtures()
    packages = {family: json.loads(path.read_text())["options"]
                for family, path in zip(fixtures, base.language.ranked.FILES, strict=True)}
    ranks = {1: "fallback", 2: "second choice", 3: "strongest choice"}
    for row in base.observations():
        family, role, identity, rotation, _ = row["observation"]
        task = fixtures[family]
        choices = []
        for label, index in zip("ABC", base.order(rotation), strict=True):
            grades = task.cards[role][index]
            terms = [f"{ranks[g]}: {display(p)}" for p, g in zip(packages[family], grades, strict=True) if g]
            choices.append(f"{label}. " + "; ".join(terms) + ". All other packages rejected.")
        content = "\n".join((f"Fictional {family} workshop. Match this mandate to a disclosure.",
                             "A match has the same policy terms at each permitted preference grade.",
                             "Your private mandate:", base.MANDATES[family][role][identity],
                             "Possible disclosures:", *choices,
                             "D. Withhold the card because no match can be established."))
        yield {**row, "messages": [row["messages"][0], {"role": "user", "content": content}]}


def hashes():
    return {**base.hashes(), Path(__file__).name: sha256(Path(__file__).read_bytes()).hexdigest()}


@contextmanager
def inputs():
    scorer = base.language.scorer
    with base.inputs(), patch.object(scorer, "observations", new=observations), \
         patch.object(scorer, "hashes", new=hashes):
        yield


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("directory", type=Path)
    cli.add_argument("--model", type=Path, required=True)
    args = cli.parse_args()
    with inputs():
        base.language.scorer.score(args.model, args.directory)
