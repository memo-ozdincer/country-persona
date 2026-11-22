"""Isolate the missing comparison that removes the canonical routing benefit."""
import json
import numpy as np

from score import held, prior, read


def main():
    result = read("scoped-drafting/results.json")
    tables = {name: np.array(value) for name, value in result["tables"].items()}
    case = read("case.json")
    index = 6 + 2 * [row["id"] for row in case["delegate"]].index("united_states")
    index += [row["id"] for row in case["clause"]].index("reporting")
    native = tables["canonical/screened"]
    authored = tables["canonical/authored"]
    assert native[index] == 52 and authored[index] == 70
    swapped = native.copy()
    swapped[index] = authored[index]
    assert np.array_equal(swapped, authored)
    tables["canonical/registered_us_only"] = swapped
    results = {}
    for name in ("canonical/screened", "canonical/registered_us_only"):
        chosen = {
            "canonical/authored": authored,
            "canonical/source_only": tables["canonical/source_only"],
            name: tables[name],
        }
        oracle = held(chosen, {}, prior.plan())[name]["summary"]
        scores = {arm: oracle[f"oracle/{arm}"]["utility"] for arm in ("arrival_only", "peer")}
        results[name] = scores | {"headroom": round(scores["peer"] - scores["arrival_only"], 8)}
    print(json.dumps({"replaced_receipt": "united_states/reporting", "simulation": results}, indent=2))


if __name__ == "__main__":
    main()
