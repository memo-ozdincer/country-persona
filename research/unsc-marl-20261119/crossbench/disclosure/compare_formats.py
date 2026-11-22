"""Compare the two measured interface runs without repairing rejected messages."""
import json
from pathlib import Path

from protocol import HERE, family_inputs, request


def read(path):
    return json.loads(path.read_text())


def compare():
    base = HERE / "evidence"
    scalar = HERE / "scalar" / "evidence"
    rb, rs = read(base / "replay.json"), read(scalar / "replay.json")
    assert rb["records"] == rs["records"] == 10
    assert rb["optimizer_updates"] == rs["optimizer_updates"] == 0
    _, _, ref = family_inputs()
    list_rows = {r["id"]: r for line in (base / "transcript.jsonl").read_text().splitlines() for r in [json.loads(line)]}
    scalar_rows = {r["id"]: r for line in (scalar / "transcript.jsonl").read_text().splitlines() for r in [json.loads(line)]}
    discarded_false = []
    table = {}
    for key in list_rows:
        old, new = list_rows[key], scalar_rows[key]
        assert old["messages"][0] == new["messages"][0] and old["cap"] == new["cap"]
        role = 0 if "-1-" in key else 1
        variant = "impasse" if key.endswith("-impasse") else "overlap"
        old_payload = json.loads(old["messages"][1]["content"])
        new_payload = json.loads(new["messages"][1]["content"])
        assert old_payload["role_view"] == new_payload["role_view"]
        if key.startswith("open"):
            assert old_payload.keys() == new_payload.keys() == {"role_view", "task"}
        if old["judgment"]["kind"] == "invalid_format":
            raw = json.loads(old["output"])
            assert len(raw["accepts"]) + len(raw["excludes"]) > 1
            own = set(ref[variant]["allowed_by_role"][role])
            if not set(raw["accepts"]) <= own or set(raw["excludes"]) & own:
                discarded_false.append(key)
        table[key] = [old["judgment"]["kind"], new["judgment"]["kind"]]
    visible = {}
    for v in ref:
        for label, records in (("lists", list_rows), ("scalar", scalar_rows)):
            visible[f"{v}/{label}"] = sum(
                json.loads(records[f"peer-{role}-{v}"]["messages"][1]["content"])["peer_preceding_admitted_disclosure"] is not None
                for role in (1, 2))
    return {
        "turn_validation": table, "discarded_list_outputs_with_false_claims": discarded_false,
        "peer_turns_with_admitted_opening_seen": visible,
        "states": {v: {arm: {k: r["outcomes"][v][arm]["readout"]["state"]
                              for k, r in (("lists", rb), ("scalar", rs))}
                       for arm in ("opening", "solo", "peer")} for v in ref},
    }


if __name__ == "__main__":
    print(json.dumps(compare(), indent=2))
