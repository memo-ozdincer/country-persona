"""Measure the value of an exact repeat review using already scored paired rows."""
import json
from hashlib import sha256
from pathlib import Path
from statistics import mean

HERE = Path(__file__).resolve().parent
TEAM = "interval_team"
EPS = 1e-7


def run():
    source = HERE / "results.json"
    archive = json.loads(source.read_text())
    rows = archive["rows"]
    clean = {(r["case"], r["law"], r["prior_information"]): r for r in rows if r["review_offset"] == 0}
    pairs = []
    for row in rows:
        if row["expanded_searches"].get(TEAM, {}).get("qualified") is not False:
            continue
        key = (row["case"], row["law"], row["prior_information"])
        exact = clean[key]
        assert row["opening"] == exact["opening"]
        before, after = row["updated"][TEAM], exact["updated"][TEAM]
        pairs.append({"case": key[0], "law": key[1], "prior_information": key[2], "offset": row["review_offset"],
                      "before": before, "clean_review": after, "net_gain_before_review_cost": after["net"] - before["net"]})
    changes = [r["net_gain_before_review_cost"] for r in pairs]
    return {"triggered": len(pairs), "triggered_already_clean": sum(r["offset"] == 0 for r in pairs),
            "before_below_silence": sum(r["before"]["over_informed_silence_quality"] < -EPS for r in pairs),
            "clean_review_below_silence": sum(r["clean_review"]["over_informed_silence_quality"] < -EPS for r in pairs),
            "net_change": {"wins": sum(v > EPS for v in changes), "losses": sum(v < -EPS for v in changes),
                           "ties": sum(abs(v) <= EPS for v in changes), "mean": mean(changes)},
            "pairs": pairs, "input_sha256": sha256(source.read_bytes()).hexdigest()}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
