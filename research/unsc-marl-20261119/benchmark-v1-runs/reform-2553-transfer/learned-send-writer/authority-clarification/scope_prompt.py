"""Run the frozen paired chair comparison with one authority clarification."""
import argparse
from importlib.util import module_from_spec, spec_from_file_location
import json
from pathlib import Path
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
PARENT = HERE.parent
spec = spec_from_file_location("paired_2553_original", PARENT / "writer.py")
baseline = module_from_spec(spec)
spec.loader.exec_module(baseline)
original_lock = baseline.locked
CLARIFICATION = (
    " Keep draft leadership and reform authority separate. South Africa led the draft. "
    "The country receiving reform assistance has the role in setting that assistance."
)


def plan():
    result = original_lock()
    for row in result["requests"].values():
        row["request"]["messages"][0]["content"] += CLARIFICATION
    result["pins"].update({str(p.relative_to(baseline.RUNS.parent)): baseline.pin(p)
                           for p in (Path(__file__), HERE / "protocol.md", PARENT / "plan.json",
                                     PARENT / "scores.json", PARENT / "verified.json")})
    return result


def locked():
    result = plan()
    assert result == baseline.test.READ(HERE / "plan.json")
    return result


def act(command):
    protocol = locked()
    with patch.object(baseline, "HERE", HERE), patch.object(baseline, "OUT", HERE / "evidence"), patch.object(
            baseline, "locked", return_value=protocol):
        if command == "run":
            baseline.run()
        else:
            verified = baseline.verify()
            launch = baseline.test.READ(HERE / "evidence/launch.json")
            assert launch["protocol_sha256"] == baseline.pin(HERE / "protocol.md")
            print(json.dumps(verified, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("plan", "run", "verify"))
    mode = parser.parse_args().mode
    if mode == "plan":
        print(json.dumps(plan(), ensure_ascii=False, indent=2))
    else:
        act(mode)
