"""Check that the independently scoped minimum evidence fits under the cap."""
import evaluate_somalia as q

case = q.n.read(q.t.SOURCE)
deck = q.t.plan()
assert deck == q.n.read(q.t.HERE / "plan.json")
chosen = {"china": ["9", "2"], "somalia": ["8", "5"], "us": ["7", "3"]}
result = q.render(case, deck["spans"], chosen, 7)
assert all(ids <= set(result["used"][role]) for role, ids in q.COMPLETE.items())
assert set(result["comparison"]) == set(q.INTERACTIONS)
q.e.emit({"words": result["words"], "output": result["text"], "pair": deck["calibration_pair"]})
