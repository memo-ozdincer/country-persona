"""Replay target preference fitting, held-out controls, and archived UN evidence."""
import json

import confirmation_target
import lookup
import targeting


EVIDENCE = lookup.HERE / "evidence" / "targeting"


def archived(name):
    return json.loads((EVIDENCE / f"{name}.json").read_text())


def same(actual, expected):
    assert json.loads(json.dumps(actual)) == expected


def main():
    launch = archived("launch")
    for path, digest in launch["sha256"].items():
        assert lookup.digest(lookup.ROOT / path) == digest, path

    rows = list(targeting.training())
    assert all(targeting.play(row, {}) == lookup.play(row, {}) for row in rows)
    policy, training_log = targeting.fit(rows)
    same(training_log, archived("training"))
    same(targeting.freeze(policy), archived("policy"))
    assert targeting.restore(archived("policy")) == policy

    sample_sizes = {}
    for name, panel in (
        ("width-5", list(lookup.examples((5,), targeting.TEST_SEED + 5, stress=True))),
        ("width-6", list(lookup.examples((6,), targeting.TEST_SEED + 6, stress=True))),
        ("fresh-7", targeting.fresh()),
    ):
        same(targeting.evaluate(panel, policy), archived(name))
        sample_sizes[name] = len(panel)

    replay = confirmation_target.evaluate()
    same(replay, archived("workshop-targets"))
    previous = json.loads(
        (EVIDENCE.parent / "fit" / "workshop-confirmation.json").read_text()
    )["metrics"]
    for family in ("sanctions", "membership"):
        for new, old in (("correct", "certificates"), ("checks", "checks"), ("slots", "slots")):
            assert replay["metrics"][f"{family}/peer_two/{new}"] == previous[
                f"{family}/confirmation_model/{old}"
            ]
    for name, trace in replay["traces"].items():
        assert sum(event["turn"] >= 0 for event in trace["events"]) <= 8
        check_limit = 2 if name.endswith("/peer_two") else 1
        assert sum("checked" in event for event in trace["events"]) <= check_limit

    print(json.dumps({
        "launch_hashes": len(launch["sha256"]),
        "training_presentations": len(rows),
        "held_out_presentations": sample_sizes,
        "workshop_replays": len(replay["traces"]),
        "first_target_controls": len(replay["target_controls"]),
        "archived_two_check_baseline_exact": True,
    }, indent=2))


if __name__ == "__main__":
    main()
