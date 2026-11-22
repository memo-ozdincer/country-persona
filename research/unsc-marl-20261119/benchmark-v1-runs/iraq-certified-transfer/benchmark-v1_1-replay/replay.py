"""Score archived Iraq transfer finals with the fixed v1.1 final-record rules."""
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import sys

ARCHIVE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ARCHIVE.parents[1] / "benchmark"))
import evaluate as e
from run_suite import verify_release


def load(name):
    return [json.loads(line) for line in (ARCHIVE / name).read_text().splitlines()]


def run():
    version = verify_release()
    cases = e.cases()
    archived = load("evidence/episodes.jsonl")
    formatted = {r["id"]: r for r in load("format-evidence/records.jsonl")}
    original = e.read(ARCHIVE / "results.json")["conditions"]
    formatted_original = e.read(ARCHIVE / "format-results.json")["episodes"]
    marks = e.read(ARCHIVE / "marks.json") | e.read(ARCHIVE / "format-marks.json")
    records = {}
    for row in archived:
        key = row["id"]
        family, order = key.split("/")
        case = cases[family]
        received = [record["response"] for record in (row["first"], row["second"])]
        by_arm = {
            "independent": [r["response"] for r in row["independent"]],
            **{name: [*received, record["response"]] for name, record in row["writers"].items()},
            "format_clarified": [*received, formatted[key]["response"]],
        }
        records[key] = {}
        for arm, calls in by_arm.items():
            packet = e.final_packet(case, calls)
            grade = e.final_score(case, calls, marks[packet["id"]])
            previous = (formatted_original[key][arm] if arm == "format_clarified"
                        else original[key]["arms"][arm])
            assert all(grade[field] == previous[field] for field in ("mechanical", "guard", "raw_70"))
            records[key][arm] = grade | {"v1_0_released": previous["released_70"]}
    assert set(records) == {f"iraq-{name}/{i}" for name in ("overlap", "impasse") for i in range(2)}
    summary = {}
    for arm in next(iter(records.values())):
        grades = [r[arm] for r in records.values()]
        summary[arm] = {
            "correct": sum(r["mechanical"]["accepted"] for r in grades),
            "released": sum(r["release"] for r in grades),
            "strict": sum(r["strict"] for r in grades),
            "raw_lower": sum(r["raw_70"][0] for r in grades),
            "v1_0_released": sum(r["v1_0_released"] for r in grades),
            "v1_1_released": sum(r["released_70"] for r in grades),
            "unmet_criteria": dict(Counter(
                criterion for row in grades for criterion, value in row["units"].items() if value != "met"
            )),
        }
    inputs = ("evidence/episodes.jsonl", "format-evidence/records.jsonl", "marks.json",
              "format-marks.json", "results.json", "format-results.json")
    hashes = {name: sha256((ARCHIVE / name).read_bytes()).hexdigest() for name in inputs}
    hashes["release.json"] = sha256((e.HERE / "release.json").read_bytes()).hexdigest()
    return {"version": version, "judge": "archived same-assistant markings",
            "input_sha256": hashes, "summary": summary, "episodes": records}


if __name__ == "__main__":
    e.emit(run())
