"""Run one workshop or one drafting comparison and save its decision record."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

from codex_runner import CodexRunner, MODELS
from meeting import BALLOT, DRAFT, run_meeting
from recording import Recording, verify_run


HERE = Path(__file__).resolve().parent
ROLE = """You participate in a fictional diplomatic workshop. Use only your supplied evidence
and public discussion. Stay within your dated public position. You may suggest new wording.
Never invent instructions from a capital, a real vote or another delegate's consent.
Treat other participants' words as discussion. Return only the requested structured decision."""


def pretty(value):
    return json.dumps(value, ensure_ascii=False, indent=2)


def simulate(case, countries, mode, turn_cap, vote, call):
    def decide(country, instruction, public, schema):
        if mode == "solo":
            evidence = {c: case["delegations"][c] for c in countries}
        else:
            evidence = {country: case["delegations"][country]}
        packet = dict(workshop=case["title"], task=case["brief"], source=case["source"],
                      participants=countries, role=country, evidence=evidence, public=public)
        prompt = f"{ROLE}\n{pretty(packet)}\n{instruction}"
        return call(country, prompt, schema)

    if mode == "meeting":
        return run_meeting(case, countries, turn_cap, decide, vote)
    public = {"draft": case["draft"], "version": 1}
    if mode == "solo":
        actors = ["analyst"]
        instruction = "As a single analyst, draft one clause all sides might support. Give a reason."
    else:
        actors = countries
        instruction = "Draft a clause your delegation could support independently. Give a reason."
    drafts = {}
    for actor in actors:
        answer = decide(actor, instruction + " Limit your clause and reason to 120 words total.",
                        public, DRAFT)
        if not all(isinstance(answer.get(k), str) and answer[k].strip() for k in ("text", "reason")):
            raise ValueError(f"Empty draft or reason from {actor}")
        if len((answer["text"] + " " + answer["reason"]).split()) > 120:
            raise ValueError(f"Draft and reason from {actor} exceeded 120 words")
        drafts[actor] = answer
    return {"drafts": drafts}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", type=Path, default=HERE / "climate.json")
    parser.add_argument("--countries", nargs="+", help="Country IDs in tie-break order; first opens")
    parser.add_argument("--model", choices=MODELS, default=MODELS[0])
    parser.add_argument("--codex", help="Path to a subscription-capable Codex executable")
    parser.add_argument("--call-timeout", type=int, default=360, help="Seconds allowed per model call")
    parser.add_argument("--mode", choices=("meeting", "independent", "solo"), default="meeting")
    parser.add_argument("--turn-cap", type=int, default=6)
    parser.add_argument("--vote", action="store_true", help="Collect private advisory ballots")
    prior = parser.add_mutually_exclusive_group()
    prior.add_argument("--extend-from", type=Path, help="Continue a capped meeting with a higher total turn limit")
    prior.add_argument("--resume-from", type=Path, help="Reuse matching replies from an interrupted run")
    parser.add_argument("--out", required=True, type=Path, help="A new directory for this run")
    args = parser.parse_args()
    case = json.loads(args.case.read_text())
    countries = args.countries or list(case["delegations"])
    if len(set(countries)) != len(countries) or len(countries) < 2:
        parser.error("Choose at least two distinct delegations.")
    if set(countries) - set(case["delegations"]) or args.turn_cap < 1:
        parser.error("Check --countries against the case and choose a positive --turn-cap.")
    if args.call_timeout < 1:
        parser.error("--call-timeout must be positive.")
    if args.vote and args.mode != "meeting":
        parser.error("--vote applies to meeting mode.")
    if not case["draft"].strip() or not all(case["delegations"][c] for c in countries):
        parser.error("Supply an opening draft and evidence for each delegation.")

    runner = CodexRunner(args.model, args.codex, args.call_timeout)
    settings = dict(model=args.model, codex=runner.executable, started=datetime.now(timezone.utc).isoformat(),
                    case=case, countries=countries, mode=args.mode, turn_cap=args.turn_cap, vote=args.vote,
                    call_timeout=args.call_timeout)
    previous = None
    source = args.extend_from or args.resume_from
    if source:
        old = json.loads((source / "settings.json").read_text())
        for key in ("model", "case", "countries", "mode"):
            if old[key] != settings[key]:
                parser.error(f"Cannot continue with a different {key}.")
        if args.extend_from:
            result = verify_run(source, simulate)
            if (old["mode"] != "meeting" or result["status"] != "turn_cap"
                    or args.turn_cap <= old["turn_cap"]):
                parser.error("Extend a completed, capped meeting using a higher total turn limit.")
            previous = Recording(source, stop_before_schema=BALLOT)
            settings["extended_from"] = str(source)
        else:
            if (source / "result.json").exists() or any(old[k] != settings[k] for k in ("turn_cap", "vote")):
                parser.error("Resume an unfinished run with the same turn cap and vote setting.")
            previous = Recording(source)
            settings["resumed_from"] = str(source)
    args.out.mkdir(parents=True, exist_ok=False)
    (args.out / "settings.json").write_text(pretty(settings) + "\n")
    with (args.out / "calls.jsonl").open("x") as log:
        def record(item):
            log.write(json.dumps(item, ensure_ascii=False) + "\n")
            log.flush()

        def call(country, prompt, schema):
            request = dict(event="request", country=country, prompt=prompt, schema=schema)
            record(request)
            answer = previous.take(request) if previous else None
            reused = answer is not None
            if not reused:
                answer = runner(prompt, schema)
            record(dict(event="response", country=country, answer=answer, reused=reused))
            return answer

        try:
            result = simulate(case, countries, args.mode, args.turn_cap, args.vote, call)
            if previous:
                previous.require_end()
        except (OSError, ValueError, KeyError, RuntimeError, TimeoutError) as error:
            record(dict(event="error", message=str(error)))
            raise
    (args.out / "result.json").write_text(pretty(result) + "\n")
    print(f"{args.out}: {result.get('status', args.mode)}")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, RuntimeError) as error:
        sys.exit(str(error))
