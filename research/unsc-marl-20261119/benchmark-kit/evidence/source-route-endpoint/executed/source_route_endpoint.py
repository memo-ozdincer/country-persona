"""Compare one frozen chair across every packet induced by three routing policies."""
import argparse
from hashlib import sha256
from itertools import product
import json
from pathlib import Path
from unittest.mock import patch

import numpy as np

import source_record_run as runner
from source_record_compact import FINAL
from source_record_episode import PACK
from source_route_fit import CASE
import source_route_memos as memo
from source_route_signal import CAPS, PHASES, POLICIES, SIGNAL_COST, terminal_matrix

HERE = Path(__file__).resolve().parent
FIT = HERE.parent / "evidence/source-route-signal/coverage-fit.json"
CARDS = ((None, "RU-A", "RU-B"), (None, "CN-A", "CN-B"))


def traces():
    data = json.loads(FIT.read_text())
    prior = np.array(CAPS)
    controls = data["exact_controls"]
    payoff = terminal_matrix(controls["public"], controls["weights"])
    policies = [POLICIES[:, prior[:, seat]] for seat in (0, 1)]
    values = payoff[policies[0][:, None], policies[1][None, :]]
    arms = {}
    for arm, bits, ceiling in (
        ("optimal_silent", np.zeros_like(prior), "net_return_ceiling_silent"),
        ("always_announce", (prior & 2) != 0, "net_return_ceiling_always_announce"),
    ):
        actions = np.zeros_like(prior)
        for phase in PHASES:
            matching = np.all(bits == phase, axis=1)
            index = np.unravel_index(values[..., matching].sum(axis=-1).argmax(), values.shape[:2])
            actions[matching] = np.stack([policies[s][index[s], matching] for s in (0, 1)], axis=1)
        outcome = payoff[actions[:, 0], actions[:, 1]] - SIGNAL_COST * bits.sum(axis=1)
        assert np.isclose(outcome.mean(), controls[ceiling])
        arms[arm] = [{"private": inventory, "signals": signal.tolist(), "evidence": action.tolist(),
                      "return": float(value)}
                     for inventory, signal, action, value in zip(CAPS, bits, actions, outcome, strict=True)]
    arms["learned"] = data["learned"]["coordinated"]["worlds"]
    assert all([list(row["private"]) for row in arm] == prior.tolist() for arm in arms.values())
    return arms


def label(evidence):
    return "packet-" + "".join(map(str, evidence))


def suite():
    case = json.loads(CASE.read_text())
    protocol = json.loads(PACK.read_text())["protocol"]
    task = (
        protocol["shared_task"] + " " + FINAL + " Include the complete recorded vote and the draft's "
        "proposed measures. State each supplied delegation's distinct position or qualification. "
        "State documented overlap only if supported by a statement from each delegation. Cite both. "
        "Do not invent omitted national positions or assume that a draft created any authority."
    )
    sources = {k: v for portfolio in case["delegate_evidence"].values() for k, v in portfolio.items()}
    packets = {tuple(row["evidence"]) for arm in traces().values() for row in arm}
    assert packets == set(product(range(3), repeat=2))
    for actions in sorted(packets):
        ids = [CARDS[seat][action] for seat, action in enumerate(actions) if action]
        packet = {**case["docket"], **{key: sources[key] for key in ids}}
        yield {"id": f"{case['family']}/{label(actions)}/chair", "evidence_ids": list(packet), "seen": [],
               "cap": protocol["generation_ceiling"]["chair"], "messages": [
                   {"role": "system", "content": "You are a neutral historical record writer. The dated evidence is the only factual authority."},
                   {"role": "user", "content": json.dumps({"task": task, "evidence": packet, "working_text": []},
                                                         ensure_ascii=False)},
               ]}


def locks():
    dependencies = ["source_record_run.py", "source_route_memos.py", "source_route_signal.py",
                    "source_route_fit.py", "source_record_compact.py", Path(__file__).name]
    paths = (CASE, FIT, PACK, *(HERE / name for name in dependencies))
    return {str(p.relative_to(HERE.parent)): sha256(p.read_bytes()).hexdigest() for p in paths}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("run", "replay", "check"))
    parser.add_argument("directory", type=Path, nargs="?")
    parser.add_argument("--model", type=Path)
    args = parser.parse_args()
    if args.mode == "check":
        print(json.dumps({"arms": traces(), "inputs": list(suite()), "sha256": locks()},
                         indent=2, ensure_ascii=False))
    elif args.mode == "run":
        if args.directory is None or args.model is None:
            parser.error("directory and --model are required for inference")
        with patch.multiple(memo, suite=suite), patch.multiple(runner, episode=memo.episode, locks=locks):
            runner.run(args.model, args.directory)
    else:
        if args.directory is None:
            parser.error("directory is required for replay")
        with patch.multiple(memo, suite=suite, locks=locks):
            print(json.dumps(memo.replay(args.directory, expected_records=9), indent=2))
