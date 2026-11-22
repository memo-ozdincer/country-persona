"""Audit the native token trace and the sealed dispatcher log."""
import argparse
from hashlib import sha256
from pathlib import Path
import sys
from unittest.mock import patch

import grade_live as grade

w, n, e = grade.w, grade.n, grade.e


def verify():
    path = w.OUT / "complete.json"
    actual = n.read(path)
    assert set(actual) == {"calls.jsonl", "tokens.jsonl", "launch.json", "dispatch.json"}
    assert all(sha256((w.OUT / name).read_bytes()).hexdigest() == digest for name, digest in actual.items())
    read = n.read

    def token_manifest(input_path):
        if input_path == path:
            return {k: v for k, v in actual.items() if k != "dispatch.json"}
        return read(input_path)

    with patch.object(n, "read", token_manifest):
        return w.verify() | {"dispatch_sha256": actual["dispatch.json"], "dispatch_replayed": True}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("verify", "score"))
    parser.add_argument("--causal", action="store_true")
    args = parser.parse_args()
    action = verify if args.mode == "verify" else grade.run
    if args.causal:
        sys.path.insert(0, str(Path(__file__).resolve().parent / "causal"))
        import causal_live as c
        with patch.multiple(w, HERE=c.HERE, OUT=c.OUT, settings=c.settings, plan=c.plan), patch.object(
                grade, "HERE", c.HERE):
            e.emit(action())
    else:
        e.emit(action())
