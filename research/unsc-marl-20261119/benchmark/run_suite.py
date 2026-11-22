"""Collect model calls or score them through a persistent JSON-lines adapter."""
import argparse
from contextlib import contextmanager
from hashlib import sha256
from itertools import product
import json
from pathlib import Path
import subprocess

import evaluate as e
import report


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
                return json.loads(line)

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
                if step == 0 and arm == "independent":
                    opening = payload, reply
                responses.append({"request_sha256": e.checksum(request), **reply})
                calls = e.validate_calls(case, arm, order, responses)
            append(directory / "episodes.jsonl",
                   {"id": f'{case["id"]}/{arm}/{order}', "calls": responses})


def adjudicate(call, directory, input_path):
    cases, episodes = report.validate_episodes(report.load(input_path))
    verdicts = []
    seen = {}
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
        item = dict(episode)
        for mode, (system, data) in prompts.items():
            request = {"max_output_tokens": 4096, "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": json.dumps(data, ensure_ascii=False)},
            ]}
            key = (mode, data["id"])
            reused = key in seen
            response = seen[key] if reused else call(request)
            seen[key] = response
            append(directory / "judges.jsonl", {"id": episode["id"], "mode": mode,
                                                "request": request, "reply": response, "reused": reused})
            e.require(response["termination"] == "complete", "Judge call did not complete. Raw output is saved.")
            item[mode] = json.loads(response["text"])
        e.final_score(case, calls, item["final"])
        e.process_score(case, calls, item["process"])
        append(directory / "validated.jsonl", item)
        verdicts.append(item)
    output = report.run(verdicts)
    output["review_status"] = "single unadjudicated reading"
    (directory / "comparison.json").write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("collect", "judge"))
    parser.add_argument("config", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--input", type=Path, help="The actor run's episodes.jsonl")
    args = parser.parse_args()
    version = verify_release()
    if args.mode == "judge" and not args.input:
        parser.error("judge requires --input")
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
        else:
            adjudicate(call, args.output, args.input)


if __name__ == "__main__":
    main()
