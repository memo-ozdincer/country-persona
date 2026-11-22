"""Give the ambiguous all-source record the benefit of the doubt."""
import json

import attributed_writer as a

rows = a.n.read(a.HERE / "results.json")["records"]
full = rows["7"]
assert full["guard"] == "uncertain" and full["release_blockers"] == ["guard_uncertain"]
points = {int(mask): row["released_70"] for mask, row in rows.items()}
points[7] = full["raw_70"][0]
print(json.dumps(a.n.comparison(points), indent=2))
