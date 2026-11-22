"""Collect, judge or calibrate through a persistent JSON-lines adapter."""
import argparse
from contextlib import contextmanager
from hashlib import sha256
from itertools import product
import json
from pathlib import Path
import subprocess

import calibrate
import evaluate as e
import report

JUDGE_BUDGET = 4096


def pin(path):
    return sha256(path.read_bytes()).hexdigest()


def verify_release():
    manifest = e.read(e.HERE / "release.json")
    for name, digest in manifest["sha256"].items():
        e.require(pin(e.HERE / name) == digest, f"Frozen release file changed: {name}")
    return manifest["version"]


def append(path, row):
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(row, ensure_ascii=False) + "\n")


@contextmanager
def worker(command, log_path):
    e.require(isinstance(command, list) and command and all(isinstance(x, str) and x for x in command),
              "Adapter command must be a nonempty JSON array of strings")
    with log_path.open("w", encoding="utf-8") as log:
        with subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                              stderr=log, text=True, encoding="utf-8") as process:
            def call(request):
                process.stdin.write(json.dumps(request, ensure_ascii=False) + "\n")
                process.stdin.flush()
                line = process.stdout.readline()
                e.require(bool(line), f"Adapter closed stdout. See {log_path}")
                try:
                    return json.loads(line)
                except json.JSONDecodeError:
                    return line

            try:
                yield call
            finally:
                process.stdin.close()


def collect(call, directory):
    for case, order in product(e.cases().values(), (0, 1)):
        opening = None
        for arm in e.ARMS:
            responses = []
            calls = []
            for step in range(3):
                request = e.build_request(case, arm, order, calls)
                reused = step == 0 and arm == "peer"
                payload = {key: request[key] for key in ("messages", "max_output_tokens")}
                if reused:
                    e.require(payload == opening[0], "Paired opening prompts differ")
                    reply = opening[1]
                else:
                    reply = call(payload)
                append(directory / "actors.jsonl", {"id": request["id"], "request": request,
                                                    "reply": reply, "reused": reused})
                e.require(isinstance(reply, dict), f"Malformed actor response for {request['id']}. See actors.jsonl")
                if step == 0 and arm == "independent":
                    opening = payload, reply
                responses.append({"request_sha256": e.checksum(request), **reply})
                calls = e.validate_calls(case, arm, order, responses)
            append(directory / "episodes.jsonl",
                   {"id": f'{case["id"]}/{arm}/{order}', "calls": responses})


def judge_request(system, packet):
    return {"max_output_tokens": JUDGE_BUDGET, "messages": [
        {"role": "system", "content": system},
        {"role": "user", "content": json.dumps(packet, ensure_ascii=False)},
    ]}


def decode_verdict(response):
    e.require(isinstance(response, dict) and set(response) ==
              {"text", "input_tokens", "output_tokens", "termination"}, "Malformed judge response")
    e.require(type(response["input_tokens"]) is int and response["input_tokens"] > 0
              and type(response["output_tokens"]) is int
              and 0 <= response["output_tokens"] <= JUDGE_BUDGET, "Invalid judge token usage")
    e.require(response["termination"] == "complete", "Judge call did not complete")
    return json.loads(response["text"])


def calibrate_judge(call, directory):
    modes = {"final": calibrate.anchors(), "process": calibrate.process_anchors()}
    summaries = {}
    failures = 0
    for mode, fixtures in modes.items():
        system = (e.HERE / f"{mode}-judge.md").read_text()
        marks = {}
        invalid = []
        for packet_id, (packet, _, *context) in fixtures.items():
            data = e.judge.request(packet) if mode == "final" else packet
            request = judge_request(system, data)
            reply = call(request)
            append(directory / "judges.jsonl", {"mode": mode, "id": packet_id,
                                                "request": request, "reply": reply})
            try:
                verdict = decode_verdict(reply)
                if mode == "final":
                    e.judge.score(packet, verdict)
                else:
                    e.process_score(*context, verdict)
            except (ValueError, KeyError, TypeError, AttributeError) as exc:
                invalid.append({"id": packet_id, "reason": str(exc)})
                continue
            marks[packet_id] = verdict
        failures += len(invalid)
        (directory / f"{mode}-verdicts.json").write_text(json.dumps(marks, ensure_ascii=False, indent=2) + "\n")
        summaries[mode] = {"expected_packets": len(fixtures), "valid_packets": len(marks),
                           "invalid": invalid, "labels": calibrate.score(marks, mode) if not invalid else None}
    receipt = {"status": "authored anchor calibration", "modes": summaries}
    (directory / "calibration.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n")
    e.require(not failures, "Incomplete anchor coverage. See calibration.json.")


def adjudicate(call, directory, input_path):
    cases, episodes = report.validate_episodes(report.load(input_path))
    items = {}
    jobs = {"final": [], "process": []}
    scorers = {"final": e.final_score, "process": e.process_score}
    for episode in episodes.values():
        name, arm, order = episode["id"].split("/")
        case = cases[name]
        calls = e.validate_calls(case, arm, int(order), episode["calls"])
        packet = e.judge.request(e.final_packet(case, calls))
        process_packet = e.process_packet(case, calls)
        prompts = {
            "final": ((e.HERE / "final-judge.md").read_text(), packet),
            "process": ((e.HERE / "process-judge.md").read_text(), process_packet),
        }
        items[episode["id"]] = {"id": episode["id"], "calls": episode["calls"]}
        for mode, (system, data) in prompts.items():
            request = judge_request(system, data)
            jobs[mode].append((data["id"], episode["id"], request, case, calls))

    failures = 0
    (directory / "valid-marks.jsonl").touch()
    for mode, requests in jobs.items():
        seen = {}
        for packet_id, episode_id, request, case, calls in sorted(requests, key=lambda job: job[0]):
            reused = packet_id in seen
            response = seen[packet_id] if reused else call(request)
            seen[packet_id] = response
            append(directory / "judges.jsonl", {"id": episode_id, "mode": mode,
                                                "request": request, "reply": response, "reused": reused})
            try:
                verdict = decode_verdict(response)
                scorers[mode](case, calls, verdict)
            except (ValueError, KeyError, TypeError, AttributeError) as exc:
                failures += 1
                append(directory / "invalid-judgments.jsonl", {
                    "episode": episode_id, "mode": mode, "packet": packet_id, "reason": str(exc),
                })
                continue
            items[episode_id][mode] = verdict
            append(directory / "valid-marks.jsonl", {"mode": mode, "verdict": verdict})
    verdicts = [item for item in items.values() if {"final", "process"} <= item.keys()]
    for item in verdicts:
        append(directory / "validated.jsonl", item)
    coverage = {"expected_episodes": len(episodes), "validated_episodes": len(verdicts),
                "invalid_logical_verdicts": failures}
    (directory / "coverage.json").write_text(json.dumps(coverage, indent=2) + "\n")
    e.require(not failures, "Incomplete judge coverage. See coverage.json and invalid-judgments.jsonl.")
    output = report.run(verdicts)
    output["review_status"] = "single unadjudicated reading"
    (directory / "comparison.json").write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("collect", "judge", "calibrate"))
    parser.add_argument("config", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--input", type=Path, help="The actor run's episodes.jsonl")
    args = parser.parse_args()
    version = verify_release()
    if args.mode == "judge" and not args.input:
        parser.error("judge requires --input")
    if args.mode != "judge" and args.input:
        parser.error("--input only applies to judge")
    config = e.read(args.config)
    args.output.mkdir()
    files = (e.HERE / "release.json", e.HERE / "cases.json", Path(__file__), args.config)
    if args.input:
        files += (args.input,)
    receipt = {"mode": args.mode, "release": version, "model": config["model"],
               "files_sha256": {str(path.resolve()): pin(path) for path in files}}
    (args.output / "launch.json").write_text(json.dumps(receipt, indent=2) + "\n")
    with worker(config["command"], args.output / "adapter.log") as call:
        if args.mode == "collect":
            collect(call, args.output)
        elif args.mode == "judge":
            adjudicate(call, args.output, args.input)
        else:
            calibrate_judge(call, args.output)


if __name__ == "__main__":
    main()
