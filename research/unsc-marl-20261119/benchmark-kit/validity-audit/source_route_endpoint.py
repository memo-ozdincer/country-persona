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
    dependencies = ["source_record_run.py", "source_route_signal.py",
                    "source_route_fit.py", "source_record_compact.py", Path(__file__).name]
    paths = (CASE, FIT, PACK, *(HERE / name for name in dependencies))
    return {str(p.relative_to(HERE.parent)): sha256(p.read_bytes()).hexdigest() for p in paths}


def episode(generate):
    batch = list(suite())
    return [{"family": batch[0]["id"].split("/")[0], "final": generate(batch)}]


def replay(directory):
    from transformers import AutoTokenizer

    launch = json.loads((directory / "launch.json").read_text())
    expected = locks()
    executed = directory / "executed"
    if executed.is_dir():
        archived = ("source_route_endpoint.py", "source_route_memos.py")
        expected.update({f"validity-audit/{name}": runner.digest(executed / name) for name in archived})
    assert launch["sha256"] == expected
    raw = directory / "transcript.jsonl"
    complete = json.loads((directory / "complete.json").read_text())
    assert complete["transcript_sha256"] == runner.digest(raw)
    tokenizer = AutoTokenizer.from_pretrained(launch["model"], local_files_only=True)
    eos = tokenizer.convert_tokens_to_ids("<|im_end|>")
    results = {}
    for request, row in zip(suite(), map(json.loads, raw.read_text().splitlines()), strict=True):
        assert all(row[key] == value for key, value in request.items())
        assert row["input_ids"] == runner.encode(tokenizer, request)
        output = row["output_ids"]
        assert 0 < len(output) <= request["cap"] and eos not in output[:-1]
        assert (output[-1] == eos) == row["ended"]
        assert tokenizer.decode(output, skip_special_tokens=True).strip() == row["output"]
        results[row["id"]] = row["output"]
    finals = directory / "final-records.json"
    assert complete["final_records_sha256"] == runner.digest(finals)
    assert results == next(iter(json.loads(finals.read_text()).values()))
    assert len(results) == complete["records"] == 9
    return {"records": len(results), "exact_replay": True}


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
        with patch.multiple(runner, episode=episode, locks=locks):
            runner.run(args.model, args.directory)
    else:
        if args.directory is None:
            parser.error("directory is required for replay")
        print(json.dumps(replay(args.directory), indent=2))
