"""Summarize matched and deduplicated explanation outcomes."""
import argparse
from collections import defaultdict
from hashlib import sha256
import json
from pathlib import Path


def run(folder):
    results = json.loads((folder / "results.json").read_text())
    typed = {row["id"]: row for row in map(json.loads, (folder / "transcript.jsonl").read_text().splitlines())}
    statistics = {}
    for group in ("all", "live", "typed"):
        for unique in (False, True):
            panels = [case for case in results if group == "all" or (case.startswith("domain")) == (group == "typed")]
            summary = {}
            for arm in ("certificate", "reasons"):
                outcomes = defaultdict(list)
                for case in panels:
                    row = typed[f"{case}/{arm}"]
                    signature = sha256(json.dumps(row["messages"], sort_keys=True).encode()).hexdigest() if unique else case
                    outcomes[signature].append(results[case][arm])
                measured = [group[0] for group in outcomes.values()]
                assert all(all(item["checked"] == group[0]["checked"] and item["strict_release"] == group[0]["strict_release"]
                               for item in group) for group in outcomes.values())
                summary[arm] = {"cases": len(measured),
                                "decision_correct": sum(r["checked"]["decision"] for r in measured),
                                "reason_correct": sum(r["checked"]["reason"] for r in measured),
                                "strict_release": sum(r["strict_release"] for r in measured),
                                "input_tokens": sum(r["input_tokens"] for r in measured),
                                "output_tokens": sum(r["output_tokens"] for r in measured)}
            statistics[f"{group}/{'distinct_prompts' if unique else 'all_rows'}"] = summary
    return statistics


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("folder", type=Path)
    print(json.dumps(run(cli.parse_args().folder), indent=2))
