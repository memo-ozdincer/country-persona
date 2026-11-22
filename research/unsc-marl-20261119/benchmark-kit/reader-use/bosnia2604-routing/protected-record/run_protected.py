"""Emit delegate statements, then attach the verified public decision."""
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
    assert len(config["anchor"].split()) + 65 <= 120
    archived = audit.get_rows()
    for arm in ARMS:
        key = f"{arm}/final"
        row = archived[key]
        source = json.loads(row["messages"][1]["content"])
        assert set(source) == {"public_record", "notes", "supplement"}
        notes = {k: source[k] for k in ("notes", "supplement")}
        messages = [{"role": "system", "content": config["instruction"]},
                    {"role": "user", "content": json.dumps(notes, ensure_ascii=False)}]
        yield {"id": key, "cap": row["cap"], "messages": messages}


def episode(generate):
    return [{"family": "bosnia2604-delegate-sections", "final": generate(list(requests()))}]


def pins():
    paths = (Path(__file__), PROTOCOL, audit.EVIDENCE / "transcript.jsonl", audit.PROTOCOL,
             Path(runner.__file__))
    return {str(p.resolve().relative_to(HERE.parent)) if p.resolve().is_relative_to(HERE.parent)
            else p.name: runner.digest(p) for p in paths}


def assemble(output):
    return audit.read(PROTOCOL)["anchor"] + "\n\n" + output


if __name__ == "__main__":
    with patch.multiple(runner, episode=episode, locks=pins):
        runner.run(MODEL, EVIDENCE)
    bodies = audit.read(EVIDENCE / "final-records.json")["bosnia2604-delegate-sections"]
    print(json.dumps({key: assemble(text) for key, text in bodies.items()}, indent=2, ensure_ascii=False))
