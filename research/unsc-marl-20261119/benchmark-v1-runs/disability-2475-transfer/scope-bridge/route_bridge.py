"""Replay the previously frozen routing matrix on both prompt and evidence axes."""
import json
from pathlib import Path
from unittest.mock import patch

import run_bridge as bridge
import route_2475 as route

HERE, PARENT, READ, prior = bridge.HERE, bridge.PARENT, bridge.READ, bridge.prior


def run():
    source = HERE / "scores.json"
    banks = READ(source)["banks"]
    read = route.READ

    def access(path):
        if Path(path) == PARENT / "scores.json":
            return {"banks": banks}
        return read(path)

    target = READ(PARENT / "routing.json")
    with patch.object(route, "READ", access):
        result = route.run()
    assert result["policy_replays"] == 432
    assert result["results"]["native/none"] == target["results"]["verbatim"]
    assert result["results"]["native/plain"] == target["results"]["compared"]
    result["sha256"]["scores.json"] = prior.digest(source)
    result["sha256"]["route_bridge.py"] = prior.digest(Path(__file__))
    return result


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, indent=2))
