"""Repeat the locked routing matrix on explicit alternate reading and authored banks."""
from pathlib import Path
from unittest.mock import patch

import route_2475 as route
from live_2475 import frozen


def run():
    oracle_path = route.HERE / "oracle.json"
    oracle = route.READ(oracle_path)
    banks = {name + "_lenient": points for name, points in oracle["lenient_un_ratification_banks"].items()}
    banks["authored_control"] = oracle["authored_bank"]
    read = route.READ

    def access(path):
        if Path(path) == route.HERE / "scores.json":
            return {"banks": banks}
        return read(path)

    with patch.object(route, "READ", access):
        result = route.run()
    assert result["policy_replays"] == 216
    del result["sha256"]["scores.json"]
    result["sha256"]["oracle.json"] = route.s.digest(oracle_path)
    result["sha256"]["sensitivity.py"] = route.s.digest(Path(__file__))
    result["purpose"] = "Retrospective guard sensitivity and authored coverage control."
    return result


if __name__ == "__main__":
    frozen.emit(run())
