"""Attribute logical inference usage to the actual stage and arm in each branch."""
from collections import defaultdict
import json

import live


def run():
    out = live.HERE / "evidence"
    episodes = live.read(out/"episodes.json")
    calls = {}
    for line in (out/"calls.jsonl").read_text().splitlines():
        row = json.loads(line)
        prompt = row["request"]["messages"][1]["content"]
        key = (row["mode"], prompt)
        assert key not in calls
        calls[key] = len(row["input_ids"]), len(row["output_ids"])
    case = live.read(live.BASE/"case.json")
    original = live.read(live.WITNESS/"plan.json")["requests"]
    system = live.read(live.BASE/"plan.json")["requests"][0]["messages"][0]["content"]
    stages = defaultdict(lambda: defaultdict(float))
    totals = defaultdict(int)

    def accumulate(branch, mode, requests):
        key = branch["setting"], branch["arm"]
        weight = branch["branch_weight"]
        for req in requests:
            n_input, n_output = calls[mode, req["messages"][1]["content"]]
            stages[key][f"{mode}_calls"] += weight
            stages[key]["input_tokens"] += weight*n_input
            stages[key]["output_tokens"] += weight*n_output
            totals[mode] += 1

    for branch in episodes["branches"]:
        # The same content builds the precise writer prompt stored in the call log.
        request = original[f'{branch["view"]}/{branch["reply"]}']
        sources = json.loads(request["messages"][1]["content"])
        if branch["arm"] == "learned" and branch["arrived"]:
            accumulate(branch, "label", live.gate_queries("early", sources["delegate_statement"],
                                                           "review", case, system))
        if branch["arrived"] and branch["reply_delivered"]:
            accumulate(branch, "write", (request,))
        if branch["source_gate_margins"] is not None:
            relation, = (name for name, sentence in live.witness.CONNECTIVES.items()
                         if branch["candidate"]["text"] == sentence)
            for side, source in (("early", "delegate_statement"), ("late", "adopted_document")):
                accumulate(branch, "label", live.gate_queries(side, sources[source], relation, case, system))
    assert dict(totals) == episodes["logical_calls"]

    results = []
    for i, summary in enumerate(episodes["summaries"]):
        data = {arm: {metric: round(value, 8) for metric, value in stages[i, arm].items()}
                for arm in ("learned", "arrival")}
        delta = data["learned"]["input_tokens"] - data["arrival"]["input_tokens"]
        results.append({"prior": summary["prior"], "usage_per_episode": data,
                        "gain": summary["gain"],
                        "break_even_cost_per_1000_extra_input_tokens":
                        round(summary["gain"]*1000/delta, 8) if delta > 0 else None})
    return results


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
