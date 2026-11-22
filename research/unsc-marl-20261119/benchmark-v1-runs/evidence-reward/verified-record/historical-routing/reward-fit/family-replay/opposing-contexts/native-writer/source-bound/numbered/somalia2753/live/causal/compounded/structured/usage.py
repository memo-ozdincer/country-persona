"""Report per-policy logical model budget from the shared native trace."""
from pathlib import Path

import structured_live as s


def run():
    execution = s.n.read(s.OUT / "dispatch.json")
    scores = s.n.read(Path(__file__).with_name("results.json"))["records"]
    released = scores["interval_team"]["score"]["released_70"]
    records = {}
    for name, record in execution["arms"].items():
        # Count opens within every arm and charge model calls even if a
        # message was lost. Experimental caching does not lower these totals.
        attempts = [turn for turn in (*execution["opening"], record["delivery"]) if turn]
        usage = {key: sum(turn["response"][key] for turn in attempts)
                 for key in ("input_tokens", "output_tokens")}
        records[name] = {"logical_model_calls": len(attempts), **usage, "n_requests": int(bool(record["query"])),
                         "released_70": scores[name]["score"]["released_70"],
                         "released_gap_vs_interval_team": scores[name]["score"]["released_70"] - released}
    tokens = s.n.lines(s.OUT / "tokens.jsonl")
    return {"paired_experiment_physical_model_calls": len(tokens), "per_policy_usage": records}


if __name__ == "__main__":
    s.e.emit(run())
