"""Score one-card controls with narrower public domains and unchanged private cards."""
import argparse
from contextlib import contextmanager
from dataclasses import replace
from hashlib import sha256
from pathlib import Path
from unittest.mock import patch

import relay_compromise_language as language

HERE = Path(__file__).resolve().parent


def panels():
    for name, task in language.ranked.fixtures().items():
        experiments = (
            ("agreement", task.first[:2], task.second, 0, task.second[0]),
            ("impasse", task.first, task.second[:2], task.first[-1], 0),
            ("ambiguous_far", task.first, task.second[:2], task.first[0], 0),
            ("ambiguous_relay", task.first[::2], task.second, 0, task.second[0]),
        )
        for label, first, second, left, right in experiments:
            narrowed = replace(task, first=first, second=second,
                               cards=(tuple(task.card(0, key) for key in first),
                                      tuple(task.card(1, key) for key in second)))
            yield name, label, narrowed, left, right


def observations():
    for family, label, task, left, right in panels():
        row = language.scene(family, task, left, right)
        yield {**row, "observation": (f"{family}/{label}", 3, left, right, False)}


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
