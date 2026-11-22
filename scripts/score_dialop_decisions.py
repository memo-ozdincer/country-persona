"""Report released human rewards and optionally compare paired, externally scored decisions."""
import argparse
import hashlib
import json
import math
import random
import statistics
import zipfile
from pathlib import Path


def paired_interval(differences):
    rng = random.Random(20261118)
    samples = sorted(statistics.mean(rng.choices(differences, k=len(differences)))
                     for _ in range(2000))
    return [samples[49], samples[1949]]


def planning_revisions(records):
    differences = []
    multiple = []
    partial = 0
    for record in records:
        result = record["result"]
        proposals = [a for a in record["action_log"] if a["type"] == "proposal"]
        complete = []
        for proposal in proposals:
            route = proposal["proposal"]
            if [stop.get("type") if stop else None for stop in route] == ["event", "travel", "event", "travel", "event"]:
                complete.append(proposal["scores"]["total"])
            else:
                partial += 1
        if not complete or complete[-1] != result["score"] or proposals[-1]["scores"]["total"] != result["score"]:
            raise ValueError("Final planning proposal differs from scored complete itinerary")
        delta = (complete[-1] - complete[0]) / (result["best"] - result["worst"])
        differences.append(delta)
        if len(complete) > 1:
            multiple.append(delta)
    return {
        "episodes": len(differences), "partial_proposals_excluded": partial,
        "episodes_with_multiple_complete_proposals": len(multiple),
        "improved": sum(d > 0 for d in differences),
        "unchanged": differences.count(0), "worsened": sum(d < 0 for d in differences),
        "mean_final_minus_first_complete": statistics.mean(differences),
        "episode_bootstrap_95": paired_interval(differences),
        "mean_delta_multiple_complete_only": statistics.mean(multiple) if multiple else None,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path, help="dialop/data.zip from the published repository")
    parser.add_argument("--pairs", type=Path, help="JSONL with task, row (zero-based), peer_score and solo_score in raw environment points")
    args = parser.parse_args()
    tasks = {}
    with zipfile.ZipFile(args.archive) as archive:
        for task in ("optimization", "itinerary", "mediation"):
            records = [json.loads(line) for line in archive.read(f"data/{task}.jsonl").splitlines()]
            if task == "itinerary":
                revisions = planning_revisions(records)
            rows = [record["result"] for record in records]
            for r in rows:
                if r["best"] <= r["worst"] or not math.isclose((r["score"] - r["worst"]) / (r["best"] - r["worst"]), r["norm"], abs_tol=1e-12):
                    raise ValueError(f"Inconsistent reference reward in {task}")
            tasks[task] = rows
    report = {task: {"human_episodes": len(rows), "human_mean_reward": statistics.mean(r["norm"] for r in rows)}
              for task, rows in tasks.items()}
    report["itinerary"]["within_episode"] = revisions
    if args.pairs:
        groups = {}
        seen = set()
        for line in args.pairs.read_text().splitlines():
            p = json.loads(line)
            task, idx = p["task"], p["row"]
            if type(idx) is not int or not 0 <= idx < len(tasks[task]) or (task, idx) in seen:
                raise ValueError("Invalid or repeated task and row")
            seen.add((task, idx))
            r = tasks[task][idx]
            arms = [p["peer_score"], p["solo_score"]]
            if any(type(x) not in (float, int) or not math.isfinite(x) for x in arms):
                raise ValueError("Both arms require a finite environment score")
            groups.setdefault(task, []).append([(x - r["worst"]) / (r["best"] - r["worst"]) for x in arms] + [r["norm"]])
        if not groups:
            raise ValueError("Empty pairs file")
        for task, episodes in groups.items():
            deltas = [peer - solo for peer, solo, _ in episodes]
            report[task]["paired"] = dict(episodes=len(episodes), mean_rewards=dict(zip(
                ("peer", "solo", "human_on_same_rows"), map(statistics.mean, zip(*episodes)))),
                peer_minus_solo=statistics.mean(deltas),
                paired_bootstrap_95=paired_interval(deltas) if len(deltas) > 1 else None)
    print(json.dumps(dict(archive_sha256=hashlib.sha256(args.archive.read_bytes()).hexdigest(), tasks=report), indent=2))


if __name__ == "__main__":
    main()
