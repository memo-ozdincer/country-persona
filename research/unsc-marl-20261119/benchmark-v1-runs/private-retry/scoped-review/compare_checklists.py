"""Compare format, guarded judgments and final choices across locked prompts."""
import json
from pathlib import Path
from statistics import mean

from delivery import replay

HERE = Path(__file__).resolve().parent


def counts(rows):
    return {arm: sum(v["valid"] for actors in rows.values() for name, mappings in actors.items()
                     if (name == "pooled") == (arm == "pooled") for v in mappings.values())
            for arm in ("pooled", "scoped")}


def inspect(data):
    out = dict(valid_reads=counts(data["verdicts"]), arms={}, delivery=replay(data))
    for arm in ("pooled", "scoped"):
        guarded = []
        for key, options in data["projected"].items():
            expected = data["archive"][key]
            guess = options[arm]
            guarded.append(dict(id=key, expected_clear=expected["guard"] == "clear",
                                clear=guess["clear"], grade=guess["grade"], expected=expected["grade"],
                                met=guess["met"], expected_met=expected["met"]))
        choices = {key: options[arm]["actual"] - options["fallback"]["actual"]
                   for key, options in data["deployments"].items()
                   if int(key.split("/")[1]).bit_count() > 1}
        out["arms"][arm] = dict(drafts=guarded, mean_absolute_grade_error=mean(abs(r["expected"]-r["grade"])
                                                                            for r in guarded),
                                delta_from_checked_fallback=choices)
    return out


if __name__ == "__main__":
    files = {
        "implicit": HERE / "results.json",
        "numbered": HERE / "indexed/results.json",
        "compact": HERE / "indexed/compact.json",
    }
    print(json.dumps({name: inspect(json.loads(path.read_text())) for name, path in files.items()}, indent=2))
