"""Run the compact judge on the same blinded candidates."""
from unittest.mock import patch

import judge
from run import HERE, MODEL, runner

INSTRUCTIONS = HERE / "judge-compact-instructions.md"
DIRECTORY = HERE / "judge-compact-evidence"


def episode(generate):
    with patch.object(judge, "INSTRUCTIONS", INSTRUCTIONS):
        return judge.episode(generate)


def pins():
    with patch.object(judge, "INSTRUCTIONS", INSTRUCTIONS):
        return {**judge.pins(), "judge_compact.py": runner.digest(HERE / "judge_compact.py")}


if __name__ == "__main__":
    with patch.multiple(runner, episode=episode, locks=pins):
        runner.run(MODEL, DIRECTORY)
