"""Verify that invalid role-local replies can consume cost but cannot enter the record."""
import argparse
import json
from pathlib import Path
from unittest.mock import patch

import live_somalia as live

e, n = live.e, live.n


def run():
    calls = {e.checksum(row["request"]): row["response"] for row in live.calls()}
    previous = n.read(live.OUT / "dispatch.json")
    rows = {}
    for label, invalid in (("foreign_id", "[9]"), ("duplicate_id", '["7","7"]')):
        def generate(request):
            data = json.loads(request["messages"][-1]["content"])
            canonical = calls[e.checksum(request)]
            if data["stage"] == "reply" and data["speaker"] == "us":
                return canonical | {"text": invalid}
            return canonical
        result = live.simulate(generate)
        summary = {}
        for arm, trace in result["arms"].items():
            source = previous["arms"][arm]
            assert trace["query"] == source["query"] and trace["cost"] == source["cost"]
            if source["reply"] == 3:
                assert trace["receipt"] == (source["receipt"] & ~4)
                assert trace["delivery"]["status"] == "invalid_role_selection"
                assert not trace["record"]["used"]["us"]
            summary[arm] = {"receipt": trace["receipt"], "cost": trace["cost"],
                            "admitted_reply": trace["delivery"]["delivered"] if trace["delivery"] else False}
        rows[label] = summary
    return rows


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--causal", action="store_true")
    if parser.parse_args().causal:
        import sys
        sys.path.insert(0, str(Path(__file__).resolve().parent / "causal"))
        import causal_live as c
        with patch.multiple(live, settings=c.settings, OUT=c.OUT, HERE=c.HERE, plan=c.plan):
            e.emit(run())
    else:
        e.emit(run())
