"""Replay the policy if the sponsors-first comparison receives overlap credit."""
import json
from unittest.mock import patch

from experiment import HERE, previous
import routing

scores = previous.base.read(HERE / "scores.json")
candidate = scores["outcomes"]["sponsors-first"]
assert candidate["known_pair"] == 56 and candidate["authored_ceiling"] == 70
assert not candidate["blockers"]
candidate["known_pair"] = candidate["authored_ceiling"]
read = previous.base.read

with patch.object(routing, "HERE", HERE), patch.object(
    previous.base, "read", side_effect=lambda path: scores if path == HERE / "scores.json" else read(path)
):
    result = routing.run()
print(json.dumps(result, ensure_ascii=False, indent=2))
