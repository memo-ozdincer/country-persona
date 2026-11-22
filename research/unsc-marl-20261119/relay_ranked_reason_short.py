"""Make certainty and the next action explicit in the explanation prompt."""
import argparse
from contextlib import contextmanager
from hashlib import sha256
import json
from pathlib import Path
from unittest.mock import patch

import relay_ranked_reason as reason

SYSTEM = (
    "Write one concise sentence, at most 32 words. Name packages by ID. "
    "Use only the certificate and give the exact decisive numbers or evidence gap. "
    "Do not repeat instructions or add an introduction."
)


def suite():
    for row in reason.suite():
        certificate = row["expected"]["certificate"]
        proof = {k: v for k, v in certificate.items() if k != "provisional"}
        if certificate["provisional"]:
            proof["wording"] = "Include 'provisionally' because one grade card is unverified."
        else:
            proof["wording"] = "Do not call the outcome provisional."
        if "missing_owner" in proof:
            proof["next_step"] = f"The chair should request the scorecard from the {proof['missing_owner']}."
        yield {**row, "messages": [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": json.dumps(proof, ensure_ascii=False)},
        ]}


def sources():
    return {**reason.sources(), Path(__file__).name: sha256(Path(__file__).read_bytes()).hexdigest()}


@contextmanager
def scenario():
    with reason.scenario(), patch.object(reason.final.generation, "suite", new=suite), \
         patch.object(reason.final.generation, "sources", new=sources):
        yield


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("directory", type=Path)
    cli.add_argument("--model", type=Path, required=True)
    args = cli.parse_args()
    with scenario():
        reason.final.generation.run(args.model, args.directory)
