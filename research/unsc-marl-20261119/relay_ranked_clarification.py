"""Ask a delegate for one precise grade when two disclosed profiles disagree."""
import argparse
from contextlib import contextmanager
from hashlib import sha256
import json
from pathlib import Path
from unittest.mock import patch

import relay_ranked_mandates as mandate
import relay_ranked_mandates_grounded as grounded

HERE = Path(__file__).resolve().parent
OPENINGS = mandate.language.ranked.relay.KIT / "evidence/relay-ranked-mandates/grounded"
ORDERS = ((0, 1, 2, 3), (2, 0, 3, 1))
GRADE = {0: "rejected", 1: "fallback", 2: "second choice", 3: "strongest choice"}


def questions():
    with grounded.inputs():
        rows = mandate.language.scorer.read(OPENINGS)
    tasks = mandate.language.ranked.fixtures()
    for (family, role, private_index, rotation, _), row in sorted(rows.items()):
        if rotation:
            continue
        # The chair is given the two leading concrete disclosures and the
        # score margin. The private index is for reply simulation only.
        scores = row["scores"]
        primary, alternative, _ = sorted(range(3), key=lambda i: (-scores[i], i))
        assert primary == max(range(4), key=scores.__getitem__)
        profiles = tasks[family].cards[role]
        varying = [i for i in range(len(profiles[primary])) if profiles[primary][i] != profiles[alternative][i]]
        position = max(varying, key=lambda i: (len({profile[i] for profile in profiles}),
                                               abs(profiles[primary][i] - profiles[alternative][i]), -i))
        yield {"key": (family, role, private_index), "claimed": primary, "alternative": alternative,
               "margin": scores[primary] - scores[alternative], "package_index": position}


def observations():
    packages = {family: json.loads(path.read_text())["options"]
                for family, path in zip(mandate.MANDATES, mandate.language.ranked.FILES, strict=True)}
    for q in questions():
        family, role, private_index = q["key"]
        package = packages[family][q["package_index"]]
        desc = grounded.display(package)
        for rotation, order in enumerate(ORDERS):
            choices = [f"{letter}. {GRADE[value]}" for letter, value in zip("ABCD", order, strict=True)]
            content = "\n".join((f"Fictional {family} workshop. Clarify one package.",
                                 "Your private mandate:", mandate.MANDATES[family][role][private_index],
                                 "Chair's question:", f"What rank does your mandate assign to {desc}?",
                                 "If the terms do not match any of the permitted combinations, answer rejected.",
                                 *choices))
            yield {"observation": (family, role, private_index, rotation, False), "legal": (0, 1, 2, 3),
                   "messages": [{"role": "system", "content": "Answer only the chair's narrow question using your own private mandate. Return the single answer letter."},
                                {"role": "user", "content": content}]}


def hashes():
    return {**grounded.hashes(), Path(__file__).name: sha256(Path(__file__).read_bytes()).hexdigest(),
            "grounded_openings": sha256((OPENINGS / "actions.jsonl").read_bytes()).hexdigest()}


@contextmanager
def inputs():
    scorer = mandate.language.scorer
    with grounded.inputs(), patch.object(scorer, "observations", new=observations), \
         patch.object(scorer, "hashes", new=hashes):
        yield


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("directory", type=Path)
    cli.add_argument("--model", type=Path, required=True)
    args = cli.parse_args()
    with inputs():
        mandate.language.scorer.score(args.model, args.directory)
