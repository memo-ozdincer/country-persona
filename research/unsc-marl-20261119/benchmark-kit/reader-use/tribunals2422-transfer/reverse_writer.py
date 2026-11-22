"""Reverse distinct multi-desk inputs while preserving all other writer settings."""
import json
from pathlib import Path
from unittest.mock import patch

import writer

EVIDENCE = writer.HERE / "reversed-writer-evidence"


def requests():
    for row in writer.requests():
        evidence = json.loads(row["messages"][1]["content"])
        if len(evidence) > 1:
            row["messages"][1]["content"] = json.dumps(evidence[::-1], ensure_ascii=False)
            yield row


def episode(generate):
    return [{"family": writer.FAMILY, "final": generate(list(requests()))}]


def locks():
    return writer.locks() | {Path(__file__).name: writer.runner.digest(Path(__file__))}


if __name__ == "__main__":
    with patch.multiple(writer.runner, episode=episode, locks=locks):
        writer.runner.run(writer.MODEL, EVIDENCE)
