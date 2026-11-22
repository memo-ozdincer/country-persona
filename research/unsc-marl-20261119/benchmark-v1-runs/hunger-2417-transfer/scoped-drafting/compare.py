"""Replay the original scoring and routing protocol with the revised drafts."""
import json
from pathlib import Path
import sys
from unittest.mock import patch

from run import HERE, PARENT, plan

sys.path.insert(0, str(PARENT))
import score


def read(name):
    root = PARENT if name == "case.json" else HERE
    return json.loads((root/name).read_text())


if __name__ == "__main__":
    with patch.object(score, "read", read), patch.object(score, "plan", plan):
        print(json.dumps(score.report(), ensure_ascii=False, indent=2))
