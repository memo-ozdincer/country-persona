"""Replay the measured withholding responses as isolated availability changes."""
from copy import deepcopy
import json

import replay_delivery as study


def run():
    parent, load = study.HERE, study.base.read
    archive = {name: load(parent / f"{name}-admission.json") for name in ("bare", "identity")}
    ordinary = load(parent / "bare-replay.json")
    assert archive["bare"]["admitted_masks"] == archive["identity"]["admitted_masks"]
    packet = load(study.base.PACKET)
    result = {}
    for label, report in archive.items():
        conditions = {}
        for sources in ((1,), (2,), (3,), (1, 2, 3)):
            trial = deepcopy(report)
            for c in sources:
                accepted = report["reports"][f"withheld/{c}"]["accepted"]
                fields = packet["cards"][c - 1]["atoms"]
                allowed = sum(1 << (2 * (c - 1) + i) for i, a in enumerate(fields) if a["id"] in accepted)
                assert allowed & trial["admitted_masks"][c][c] == allowed
                trial["admitted_masks"][c][c] = allowed
            replay = study.run(trial)
            evaluation = {}
            for prior, modes in replay["cases"].items():
                observed = modes["observed"]
                original = ordinary["cases"][prior]["observed"]
                evaluation[prior] = {
                    key: {"net": score["net"], "queries": score["queries"],
                          "delta_from_all_clauses": score["net"] - original[key]["net"]}
                    for key, score in observed.items()
                }
            conditions["/".join(str(c) for c in sources)] = {
                "admitted_masks": trial["admitted_masks"], "cases": evaluation,
                "opportunity_world": replay["selected_no_erasure_paths"]["opportunity"],
            }
        result[label] = conditions
    return result


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, indent=2))
