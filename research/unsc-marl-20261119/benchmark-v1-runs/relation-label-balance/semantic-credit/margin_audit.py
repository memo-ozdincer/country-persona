"""Check same-prompt margin movement and action changes after recapture."""
from pathlib import Path
from statistics import mean

import numpy as np

import compare as study

HERE, team, capture, e = study.HERE, study.team, study.capture, study.e


def gap(scores):
    ordered = np.sort(scores)
    return float(ordered[-1] - ordered[-2])


def run():
    current = e.read(HERE / "results.json")
    old = capture.lab.old_rows() + [e.json.loads(x) for x in (capture.lab.OUT / "calls.jsonl").read_text().splitlines()]
    previous = {tuple(r["observation"]): r for r in old}
    differences = []
    for row in capture.lines("calls.jsonl"):
        key = tuple(row["observation"])
        reference = previous[key]
        assert row["messages"] == reference["messages"] and row["legal"] == reference["legal"]
        a, pre = team.mapped(reference)
        b, post = team.mapped(row)
        hardware = "CPU to GPU" if key[0] == "routed" and key[-1] == 0 else "GPU to GPU"
        differences.append({"observation":list(key), "device_comparison":hardware,
                            "previous_gap":gap(a), "new_gap":gap(b), "label_equal":pre==post,
                            "centered_max_delta":float(abs(a - a.mean() - b + b.mean()).max())})
    cohorts = {}
    for device in ("CPU to GPU","GPU to GPU"):
        rows = [r for r in differences if r["device_comparison"] == device]
        cohorts[device] = {"pairs":len(rows),"label_changes":sum(not r["label_equal"] for r in rows),
                           "different_top_two_margins":sum(r["previous_gap"]!=r["new_gap"] for r in rows),
                           "max_centered_delta":max(r["centered_max_delta"] for r in rows),
                           "average_margin_shift":mean(abs(r["previous_gap"] - r["new_gap"]) for r in rows)}
    cases = [r for fold in current["archive_folds"].values() for r in fold["records"]] + current["myanmar"]["records"]
    matching = ("net", "checks", "relation", "frozen_review_ceiling", "query_nets")
    assert all(all(r["policies"]["staged"][k]==r["policies"]["represented"][k] for k in matching) for r in cases)
    assert len(cases) == 27
    stages = e.read(HERE.parent/"staged-results.json")
    return {"matched_prompt_comparisons":cohorts,"rows":differences,"unchanged_greedy_cases":len(cases),
            "myanmar_fixed_rule_before":e.read(HERE.parent/"route-results.json")["myanmar"]["fixed_rule"],
            "myanmar_fixed_rule_now":current["myanmar"]["fixed_rule"],
            "myanmar_fixed_net_before":stages["myanmar"]["means"]["fixed_train"]["net"],
            "myanmar_fixed_net_now":current["myanmar"]["summary"]["fixed_train"]["net"],
            "sha256":{p.name:team.pin(p) for p in (Path(__file__),HERE/"results.json",HERE/"verified.json")}}


if __name__ == "__main__":
    e.emit(run())
