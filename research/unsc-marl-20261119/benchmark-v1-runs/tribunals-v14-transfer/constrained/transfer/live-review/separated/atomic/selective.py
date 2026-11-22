"""Diagnose a conservative policy that averages labels only on scoped records."""
import json
from hashlib import sha256
from pathlib import Path
from statistics import mean

HERE = Path(__file__).resolve().parent
EPS = 1e-7


def run():
    p = HERE / "results.json"
    plan = HERE / "plan.json"
    data = json.loads(p.read_text())
    views = json.loads(plan.read_text())["routing"]
    modes = {key: "scoped" for key in data["grades"]["scoped"]}
    for criterion, view in views.items():
        if view["scoped"] != view["whole"]:
            modes[criterion.rsplit("/", 1)[0]] = "scoped_mean"
    scores = {key: data["grades"][mode][key] for key, mode in modes.items()}
    rows = []
    for row in data["rows"]:
        case = row["case"]
        mode = modes[case + "/pair"]
        measured = row["atomic"][mode]
        rows.append({k: row[k] for k in ("case", "law", "prior_information", "offset")} |
                    {"mode": mode, "admitted_grade": measured["admitted_grade"], "original": row["original"],
                     "selected": measured["performance"]})
    net = [r["selected"]["net"] - r["original"]["net"] for r in rows]
    return {"scope": "Post hoc diagnostic. The selector conditions on source-scoped inputs and uses no numerical gold grade.",
            "summary": {"accepted_records": sum(r["accepted"] for r in scores.values()),
                        "exact_records": sum(r["exact"] for r in scores.values()),
                        "exact_pairs": sum(r["exact"] and key.endswith("/pair") for key, r in scores.items()),
                        "net_mean_over_original": mean(net),
                        "net_wins": sum(x > EPS for x in net), "net_losses": sum(x < -EPS for x in net),
                        "below_informed_silence": sum(r["selected"]["over_informed_silence_quality"] < -EPS for r in rows)},
            "modes": modes, "grades": scores, "rows": rows,
            "sha256": {file.name: sha256(file.read_bytes()).hexdigest() for file in (Path(__file__), p, plan)}}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, ensure_ascii=False))
