"""Regenerate matched final records after clarifying one public phrase."""
import json
from pathlib import Path
import sys
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import audit
from run import ARMS, MODEL, runner

PROTOCOL = HERE / "protocol.json"
EVIDENCE = HERE / "evidence"


def requests():
    config = audit.read(PROTOCOL)
    assert tuple(config["arms"]) == ARMS
    archived = audit.get_rows()
    for arm in ARMS:
        key = f"{arm}/final"
        row = archived[key]
        system, user = row["messages"]
        payload = json.loads(user["content"])
        before = payload["public_record"]
        assert before.count(config["replace"]) == 1
        assert config["with"] not in before
        payload["public_record"] = before.replace(config["replace"], config["with"])
        messages = [system, {**user, "content": json.dumps(payload, ensure_ascii=False)}]
        assert user["content"].replace(config["replace"], config["with"], 1) == messages[1]["content"]
        yield {"id": key, "cap": row["cap"], "messages": messages}


def episode(generate):
    return [{"family": "bosnia2604-plain-anchor", "final": generate(list(requests()))}]


def pins():
    paths = (Path(__file__), PROTOCOL, audit.EVIDENCE / "transcript.jsonl", audit.PROTOCOL,
             Path(runner.__file__))
    return {str(p.resolve().relative_to(HERE.parent)) if p.resolve().is_relative_to(HERE.parent)
            else p.name: runner.digest(p) for p in paths}


if __name__ == "__main__":
    with patch.multiple(runner, episode=episode, locks=pins):
        runner.run(MODEL, EVIDENCE)
