"""Check the two score banks and any released routing experiment."""
from itertools import product
import json
from pathlib import Path
from statistics import mean

HERE = Path(__file__).resolve().parent


def load(directory, name):
    return json.loads((directory / name).read_text())


def audit():
    runs = [HERE, HERE/"scoped-drafting"]
    plans = [load(directory, "plan.json") for directory in runs]
    requests = [spec["requests"] for spec in plans]
    assert requests[0].keys() == requests[1].keys()
    for key, row in requests[0].items():
        a, b = row["request"], requests[1][key]["request"]
        assert a["messages"][1] == b["messages"][1] and a["messages"][0] != b["messages"][0]
        assert a["max_output_tokens"] == b["max_output_tokens"]

    proof = {}
    for directory in runs:
        result = load(directory, "results.json")
        case = load(HERE, "case.json")
        expected = probed_bounds(result)
        assert (result["screened_canonical_peer_headroom"] > 0) == bool(result["fits"])
        assert result["tables"]["canonical/authored"][6:] == [70, 52, 52, 70, 52, 52]
        for grade in result["grades"].values():
            assert grade["screened"] == max(grade["raw_released"], grade["source_only"])
            if grade["final_words"] > case["word_cap"]:
                assert grade["raw_released"] == 0
        proof["initial" if directory == HERE else directory.name] = expected
    return {"paired_prompts_checked": len(requests[0]), "results": proof}


def probed_bounds(result):
    totals = {}
    for name in ("canonical/authored", "canonical/screened", "reversed/screened"):
        rows = result["evaluation"][name]["rows"]
        table = result["tables"][name]
        assert len(rows) == 96
        for arm, tags in (("arrival_only", [1, 1, 1]), ("peer", [1, 2, 3])):
            optimum = []
            for row in rows:
                q0, q1, price, mass = row["setting"]
                best = float("-inf")
                for sender in product((False, True), repeat=3):
                    for reply in product((0, 1), repeat=1+max(tags)):
                        value = 0.
                        for i in range(3):
                            first_mass = q0 if sender[i] else 0
                            first_pay = (1-q1)*table[1+i] + q1*table[6+2*i+reply[tags[i]]]
                            absent_pay = (1-q1)*table[0] + q1*table[4+reply[0]]
                            value += mass[i]*(first_mass*first_pay+(1-first_mass)*absent_pay-price*sender[i])
                        best = max(best, value)
                optimum.append(best)
                assert abs(best-row["arms"][f"oracle/{arm}"][0]) < 1e-7
            totals[f"{name}/{arm}"] = round(mean(optimum), 8)
    return totals


if __name__ == "__main__":
    print(json.dumps(audit(), indent=2))
