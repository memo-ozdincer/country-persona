"""Test explicit peer addresses and roll-call precedence at the delegate stage."""
import argparse
from contextlib import contextmanager
import json
from pathlib import Path
from unittest.mock import patch

import minurso_deliberation as base

OPEN = (
    "Write a brief retrospective account of your own delegation for the chair. Give the national position and its "
    "stated reason, with IDs. Keep abstention and non-participation distinct and use MAIN for the final vote. "
    "Then ask one concrete question about the other participant's position or reason in this meeting only. "
    "Address the question by name to the only counterpart listed below. At most 65 words."
)
REVISE = (
    "Write your final national account, using at most 55 words. Verify every claim against your evidence. "
    "If a draft conflicts with MAIN on the formal vote, follow MAIN. National explanations must come from your "
    "own dated source. If you see a named question to your delegation, answer it only if your evidence does. "
    "Integrate the answer into your account for the chair. Cite evidence IDs. Omit unsupported guesses. "
    "Do not repeat the question. Output only the revised account."
)
BASE_MESSAGE = base.message
BASE_LOCKS = base.locks


def message(id_, system, body, evidence_ids, seen, cap):
    if not id_.startswith("chair-"):
        role = int(id_[-1])
        body = {**body, "only_counterpart": base.ROLES[1 - role]}
    return BASE_MESSAGE(id_, system, body, evidence_ids, seen, cap)


def locks():
    path = Path(__file__)
    return {**BASE_LOCKS(), path.name: base.runner.digest(path)}


@contextmanager
def parameters():
    with patch.multiple(base, OPEN=OPEN, REVISE=REVISE, message=message, locks=locks):
        yield


def review(directory, annotations):
    from minurso_deliberation_review import readout
    return readout(directory, annotations)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode", choices=("check", "run", "replay", "score"))
    p.add_argument("directory", type=Path, nargs="?")
    p.add_argument("--model", type=Path)
    p.add_argument("--annotations", type=Path)
    args = p.parse_args()
    with parameters():
        if args.mode == "check":
            print(json.dumps(base.check(), indent=2))
        elif args.mode == "run":
            if args.model is None or args.directory is None:
                p.error("run requires directory and model")
            with patch.multiple(base.runner, episode=base.episode, locks=locks):
                base.runner.run(args.model, args.directory)
        elif args.mode == "replay":
            print(json.dumps(base.replay(args.directory), ensure_ascii=False, indent=2))
        else:
            if args.annotations is None:
                p.error("score requires --annotations")
            print(json.dumps(review(args.directory, json.loads(args.annotations.read_text())), indent=2))
