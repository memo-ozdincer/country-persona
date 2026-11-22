"""Replay the exhaustively evaluated policy and inspect its unresolved cases."""
from collections import Counter
import hashlib
import json
import math
from pathlib import Path

import torch

from run import FAMILIES_PATH, HERE, Policies, TEST, exhaustive_worlds, rollout, summarize


def read(name):
    return json.loads((HERE / name).read_text())


def main():
    torch.set_num_threads(1)
    launch = read("launch.json")
    locks = (HERE / "run.py", FAMILIES_PATH, FAMILIES_PATH.with_name("environment.py"), FAMILIES_PATH.with_name("evaluate.py"))
    for path in locks:
        assert hashlib.sha256(path.read_bytes()).hexdigest() == launch["hashes"][path.name]
    expected = read("scores.json")
    baseline = read("baseline.json")
    for k, v in baseline.items():
        assert expected[k] == v
    updates = [json.loads(line) for line in (HERE / "updates.jsonl").read_text().splitlines()]
    assert [r["step"] for r in updates] == list(range(1, launch["updates"] + 1))
    grad = {}
    for name in ("question_grad_norm", "response_grad_norm"):
        assert all(math.isfinite(r[name]) for r in updates)
        grad[name] = sum(r[name] > 0 for r in updates)
        assert grad[name] > 0
    torch.manual_seed(launch["seed"])
    model = Policies()
    original = {k: p.clone() for k, p in model.state_dict().items()}
    candidates = {k: torch.tensor(v) for k, v in read("policies.json").items()}
    traces = read("selected_traces.json")
    worlds = exhaustive_worlds(TEST)
    cases = [c for c in worlds for _ in range(2)]
    leaders = [i for _ in worlds for i in (0, 1)]
    unresolved, after = Counter(), {}
    with torch.no_grad():
        for label, mode in (("binary", "binary"), ("scripted", "scripted"), ("before", "greedy")):
            assert summarize(rollout(model, cases, leaders, mode)[0]) == expected[label]
        model.load_state_dict(candidates)
        changed = [k for k, v in model.state_dict().items() if not torch.equal(original[k], v)]
        for key, mode in (("learned", "greedy"), ("counter_removed", "counter_removed")):
            arr = rollout(model, cases, leaders, mode)[0]
            assert summarize(arr) == expected[key] and arr[:96] == traces[key]
            after[key] = arr
            if key == "learned":
                for row in arr:
                    if row["final"] == "unresolved":
                        local, peer = row["case"]["mandates"]
                        if row["leader"] == 1:
                            local, peer = peer, local
                        size_pair = (sum(local), sum(peer))
                        unresolved[(row["feasible"], size_pair, row["pairs"], row["counters"])] += 1
    pair_counts = Counter(str((a["final"] != "unresolved", b["final"] != "unresolved"))
                          for a, b in zip(after["learned"], after["counter_removed"]))
    assert dict(pair_counts) == expected["paired_counter_effect"]
    print(json.dumps({
        "replayed_presentations_per_arm": len(cases), "replayed_arms": 5,
        "finite_update_records": len(updates), "nonzero_gradient_updates": grad,
        "changed_parameter_tensors": changed, "paired_counter_effect": dict(pair_counts),
        "unresolved_breakdown": [{"feasible": key[0], "mandate_sizes": key[1], "questions": key[2],
                                  "counters": key[3], "presentations": count}
                                 for key, count in unresolved.items()],
    }, indent=2))


if __name__ == "__main__":
    main()
