"""Run one matched prompt intervention on the Resolution 2739 append writer."""
import argparse
import json
from pathlib import Path
import sys
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
PRIOR = HERE.parent / "source-preserving-transfer"
OUT = HERE / "evidence"
sys.path.insert(0, str(PRIOR))
import study as previous

INSTRUCTION = (
    " Compare the stated reasons about reporting in the delivered statements. If both statements "
    "explicitly express a common purpose, state that purpose at the scope the evidence supports. "
    "Keep the voting positions distinct from the reasons and do not infer endorsement of a "
    "resolution from sharing a purpose. An adopted action alone cannot establish a delegation's reason."
)


def plan():
    original = previous.locked()
    pins = {str(p.relative_to(previous.RUNS.parent)): previous.base.collector.sha(p)
            for p in (Path(__file__), HERE / "protocol.md", PRIOR / "plan.json",
                      PRIOR / "score.py", PRIOR / "scores.json")}
    assert pins.keys().isdisjoint(original["pins"])
    requests = original["requests"]
    return {
        **original, "pins": {**original["pins"], **pins},
        "requests": {key: {**row, "messages": [
            {**row["messages"][0], "content": row["messages"][0]["content"] + INSTRUCTION},
            row["messages"][1],
        ]} for key, row in requests.items()},
    }


def locked():
    result = plan_before_patch
    assert result == previous.base.read(HERE / "plan.json")
    return result


def invoke(mode):
    if mode == "plan":
        return plan()
    if mode in ("run", "verify"):
        with patch.object(previous, "HERE", HERE), patch.object(previous, "OUT", OUT), patch.object(
            previous, "locked", locked
        ):
            return previous.act(mode)
    if mode == "score":
        import score
        with patch.object(score, "HERE", HERE):
            return score.score()
    if mode == "routing":
        import routing
        with patch.object(routing, "HERE", HERE):
            return routing.run()
    raise ValueError(mode)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("plan", "run", "verify", "score", "routing"))
    mode = parser.parse_args().mode
    plan_before_patch = plan()
    result = invoke(mode)
    if mode != "run":
        print(json.dumps(result, ensure_ascii=False, indent=2))
