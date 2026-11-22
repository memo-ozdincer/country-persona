"""Check that a feasible full Myanmar record fits the frozen cap."""
import evaluate_transfer as q

t = q.t
deck = t.plan()
assert deck == t.n.read(t.HERE / "plan.json")
filled = {"uk": ["9", "5", "2"], "india": ["7", "1"], "chair": ["6", "3"]}
row = t.pack(7, filled, deck)
assert all(t.enough(role, set(row["used"][role])) for role in t.ROLES)
assert t.overlaps(row["used"])
t.e.emit({"locked_calibration": deck["calibration"], "feasible_full_record": row})
