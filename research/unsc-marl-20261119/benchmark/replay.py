"""Replay the archived Syria final records and compare legacy and release credit."""
from collections import defaultdict

import evaluate as e

ARCHIVE = e.HERE.parent / "benchmark-v1-runs" / "syria-baseline"


def run():
    cases = e.cases()
    marks = e.read(ARCHIVE / "final-marks.json")
    legacy = e.read(ARCHIVE / "results.json")["episodes"]
    arms = defaultdict(lambda: {"rows": 0, "mechanical_correct": 0, "raw_lower": 0,
                                "v1_0_released": 0, "v1_1_released": 0})
    for line in (ARCHIVE / "evidence" / "episodes.jsonl").read_text().splitlines():
        row = e.json.loads(line)
        name, arm, order = row["id"].split("/")
        case = cases[name]
        calls = e.validate_calls(case, arm, int(order), row["calls"])
        packet = e.final_packet(case, calls)
        score = e.final_score(case, calls, marks[packet["id"]])
        old = legacy[row["id"]]
        for field in ("raw_70", "guard", "mechanical"):
            e.require(old[field] == score[field], f"Unexpected replay change to {field}")
        stats = arms[arm]
        stats["rows"] += 1
        stats["mechanical_correct"] += score["mechanical"]["accepted"]
        stats["raw_lower"] += score["raw_70"][0]
        stats["v1_0_released"] += old["released_70"]
        stats["v1_1_released"] += score["released_70"]
    e.require(set(arms) == set(e.ARMS) and all(a["rows"] == 4 for a in arms.values()), "Incomplete archive")
    return {"family": "syria", "annotation": "archived same-assistant semantic reading",
            "arms": dict(arms)}


if __name__ == "__main__":
    e.emit(run())
