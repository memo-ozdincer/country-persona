"""Repeat the same chair requests with the verified meeting date delivered."""
import argparse
from contextlib import contextmanager
import json
from pathlib import Path
from unittest.mock import patch

import mali_request_writer as base
from mali_request_writer_review import DOCKET, report

BASE_EVIDENCE, BASE_LOCKS = base.evidence, base.locks
BASE_REPLAY = base.replay


def dated_evidence():
    public, cards = BASE_EVIDENCE()
    assert "30 August 2023" in json.loads(base.MALI.read_text())["task"]
    return {"docket": DOCKET, **public}, cards


def locks():
    return {**BASE_LOCKS(), Path(__file__).name: base.runner.digest(Path(__file__))}


@contextmanager
def parameters():
    with patch.multiple(base, evidence=dated_evidence, locks=locks):
        yield


def check():
    first = list(base.requests())
    with parameters():
        second = list(base.requests())
    for a, b in zip(first, second, strict=True):
        assert a["id"] == b["id"] and a["cap"] == b["cap"]
        assert a["messages"][0] == b["messages"][0]
        assert b["evidence_ids"] == ["docket", *a["evidence_ids"]]
        before, after = (json.loads(r["messages"][1]["content"])["evidence"] for r in (a, b))
        assert after.pop("docket") == DOCKET and before == after
    return len(second)


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("mode", choices=("check", "run", "replay", "score"))
    cli.add_argument("directory", type=Path, nargs="?")
    cli.add_argument("--model", type=Path)
    cli.add_argument("--annotations", type=Path)
    cli.add_argument("--policy", type=Path)
    cli.add_argument("--joint-reader", type=Path)
    cli.add_argument("--scoped-reader", type=Path)
    cli.add_argument("--exact", action="store_true")
    args = cli.parse_args()
    if args.mode == "check":
        print(json.dumps({"requests": check(), "change": "Added the verified public meeting date to every packet."}))
    else:
        if args.directory is None:
            cli.error("directory is required")
        with parameters():
            if args.mode == "run":
                if args.model is None:
                    cli.error("run requires --model")
                with patch.multiple(base.runner, locks=locks, episode=base.episode):
                    base.runner.run(args.model, args.directory)
            elif args.mode == "replay":
                print(json.dumps(BASE_REPLAY(args.directory, verify_tokens=True), indent=2, ensure_ascii=False))
            else:
                if not all((args.annotations, args.policy, args.joint_reader, args.scoped_reader)):
                    cli.error("score requires annotations, policy, and both decoder results")
                print(json.dumps(report(args.directory, args.annotations, args.policy, args.joint_reader,
                                        args.scoped_reader, args.exact), indent=2, ensure_ascii=False))
