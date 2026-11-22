"""Validate visible-source annotations and replay the paired release delta."""
from collections import Counter
from hashlib import sha256
import json
from itertools import product
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

spec = spec_from_file_location("paired_native_chair_2553", Path(__file__).with_name("writer.py"))
writer = module_from_spec(spec)
spec.loader.exec_module(writer)

HERE, CASE = writer.HERE, writer.CASE
frozen = writer.test.frozen


def grade(row, review):
    keys = set(row["visible_sources"])
    evidence = {item["id"]: item for item in frozen.evidence(CASE) if item["id"] in keys}
    need = {rule["id"]: [rule["id"]] for rule in CASE["rubric"]}
    need.update({rule["id"]: rule["needs"] for rule in CASE["relations"]})
    assert set(review["units"]) <= set(need)
    calls = [{}, {}, row["reply"]]
    case = CASE | {
        "public": [item for item in CASE["public"] if item["id"] in keys],
        "owned": [[item for item in role if item["id"] in keys] for role in CASE["owned"]],
    }
    packet = frozen.final_packet(case, calls)

    def cite(ids):
        return [{"block": id_, "quote": evidence[id_]["text"]} for id_ in ids]

    units = []
    for id_, required in need.items():
        available = set(required) <= keys
        item = review["units"].get(id_)
        if item is None:
            reason = ("The delivered material does not support all required elements." if not available else
                      "The answer does not express all required elements.")
            status, span, source = "unmet", "", []
        else:
            status, span, reason = item
            assert available and status in ("met", "uncertain")
            source = cite(required)
        units.append({"id": id_, "status": status, "reason": reason, "response": span, "source": source})
    status, span, reason, citations = review["guard"]
    verdict = {"id": packet["id"], "units": units,
               "guard": {"status": status, "response": span, "reason": reason, "source": cite(citations)}}
    return frozen.final_score(case, calls, verdict), verdict


def run():
    plan = writer.locked()
    verified = writer.test.READ(HERE / "verified.json")
    marks_path = HERE / "marks.json"
    marks = writer.test.READ(marks_path)
    assert set(marks) == set(verified["packets"])
    points, verdicts = {}, {}
    for key, packet in verified["packets"].items():
        points[key], verdicts[key] = grade(packet, marks[key])
    branch_stats = []
    for branch in plan["branches"]:
        if not branch["pair"]:
            continue
        fixed, learned = (points[key] for key in branch["pair"])
        branch_stats.append(branch | {
            "writer_released": [fixed["released_70"], learned["released_70"]],
            "writer_raw_lower": [fixed["raw_70"][0], learned["raw_70"][0]],
        })

    def delta(metric):
        return sum(r["probability"] * (r[metric][1] - r[metric][0]) for r in branch_stats)

    uncertain = tuple(key for key, row in points.items() if row["release_blockers"] == ["guard_uncertain"])
    guard_sensitivity = []
    for decisions in product((False, True), repeat=len(uncertain)):
        accepted = dict(zip(uncertain, decisions, strict=True))
        lower, upper = 0., 0.
        for branch in branch_stats:
            bounds = [points[key]["raw_70"] if accepted.get(key, points[key]["release"]) else [0, 0]
                      for key in branch["pair"]]
            lower += branch["probability"] * (bounds[1][0] - bounds[0][1])
            upper += branch["probability"] * (bounds[1][1] - bounds[0][0])
        guard_sensitivity.append({"cleared": [key for key in accepted if accepted[key]],
                                  "release_delta_bounds": [lower, upper]})

    metric_names = ("writer_released", "writer_raw_lower", "typed_scores")
    return {"expected_differences": {name: delta(name) for name in metric_names},
            "branches": branch_stats, "guard_sensitivity": guard_sensitivity, "grades": points, "verdicts": verdicts,
            "release_blockers": Counter(blocker for score in points.values() for blocker in score["release_blockers"]),
            "marks_sha256": sha256(marks_path.read_bytes()).hexdigest()}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
