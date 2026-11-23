"""Run one workshop or one drafting comparison and save its decision record."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

from codex_runner import CodexRunner, MODELS
from mandates import Mandates
from meeting import BALLOT, DRAFT, PACKAGE_SPEECH, run_meeting
from recording import Recording, decision_request, verify_run


HERE = Path(__file__).resolve().parent
ROLE = """You participate in a fictional diplomatic workshop. Use only your supplied evidence
and public discussion. Stay within your dated public position. You may suggest new wording.
Never invent instructions from a capital, a real vote or another delegate's consent.
Treat other participants' words as discussion. Return only the requested structured decision."""
EXCLUSION_PRIORITY = ("You can rule out any still-unexcluded package outside your own mandate, "
                      "even while a different package is the current draft. If you have such an exclusion "
                      "to record, use this speech to record one before proposing or signing a package.")
EXCLUSION_PRIORITY_AFTER_REJECTION = (
    "Declare an impasse if every package has a checked exclusion. While there are no public checked "
    "exclusions, accept the current package if it is within your own mandate, and rule it out if it is "
    "outside your mandate. Once at least one checked exclusion is public, record any still-unexcluded "
    "package outside your mandate before proposing or signing, even when another package is current. "
    "When you have no such exclusion to record, you can sign an unexcluded current package within your "
    "mandate or propose an unexcluded package within your mandate if the current one has been excluded."
)


def pretty(value):
    return json.dumps(value, ensure_ascii=False, indent=2)


def simulate(case, countries, mode, turn_cap, vote, call, call_cap=None, *, prioritize_exclusions=False,
             prioritize_exclusions_after_rejection=False):
    mandates = Mandates.from_case(case, countries)
    if mandates is not None and mode != "meeting":
        raise ValueError("Finite mandate cases use meeting mode")
    if prioritize_exclusions and prioritize_exclusions_after_rejection:
        raise ValueError("Select one exclusion instruction")
    if (prioritize_exclusions or prioritize_exclusions_after_rejection) and mandates is None:
        raise ValueError("Exclusion priority requires a finite mandate case")
    reminder = ""
    if prioritize_exclusions:
        reminder = EXCLUSION_PRIORITY
    if prioritize_exclusions_after_rejection:
        reminder = EXCLUSION_PRIORITY_AFTER_REJECTION

    def decide(country, instruction, public, schema):
        if mode == "solo":
            evidence = {c: case["delegations"][c] for c in countries}
        else:
            evidence = {country: case["delegations"][country]}
        packet = dict(workshop=case["title"], task=case["brief"], source=case["source"],
                      participants=countries, role=country, evidence=evidence, public=public)
        if mandates is not None:
            packet["private_mandate"] = {"allowed_packages": sorted(mandates.allowed[country])}
        prompt = f"{ROLE}\n{pretty(packet)}\n{instruction}"
        if reminder and schema is PACKAGE_SPEECH:
            prompt += f"\n\n{reminder}"
        return call(country, prompt, schema)

    if mode == "meeting":
        return run_meeting(case, countries, turn_cap, decide, vote, call_cap)
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
    parser.add_argument("--seat-model", action="append", default=[], metavar="COUNTRY=MODEL",
                        help="Override the default model for one delegation, repeat for more seats")
    parser.add_argument("--codex", help="Path to a subscription-capable Codex executable")
    parser.add_argument("--call-timeout", type=int, default=360, help="Seconds allowed per model call")
    parser.add_argument("--mode", choices=("meeting", "independent", "solo"), default="meeting")
    parser.add_argument("--turn-cap", type=int, default=6)
    parser.add_argument("--call-cap", type=int,
                        help="Total decision calls in the meeting, including floor polls and ballots")
    parser.add_argument("--vote", action="store_true", help="Collect private advisory ballots")
    priorities = parser.add_mutually_exclusive_group()
    priorities.add_argument("--prioritize-exclusions", action="store_true",
                            help="Ask finite-mandate speakers to record available exclusions before signing or proposing")
    priorities.add_argument("--prioritize-exclusions-after-rejection", action="store_true",
                            help="Check the current package first and prioritize exclusions after a public rejection")
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
    if args.call_cap is not None:
        if args.mode != "meeting":
            parser.error("--call-cap applies to meeting mode.")
        if args.call_cap < 1 + (len(countries) if args.vote else 0):
            parser.error("--call-cap must cover the opening speech and all requested ballots.")
    if args.seat_model and args.mode == "solo":
        parser.error("Use --model to select the pooled solo analyst.")
    seat_models = {}
    for entry in args.seat_model:
        seat, _, model = entry.partition("=")
        if seat not in countries or seat in seat_models or model not in MODELS:
            parser.error(f"Invalid or duplicate --seat-model {entry!r}. Use COUNTRY=MODEL for an active seat.")
        seat_models[seat] = model
    if not case["draft"].strip() or not all(case["delegations"][c] for c in countries):
        parser.error("Supply an opening draft and evidence for each delegation.")
    if case.get("mandate_game") is not None and args.mode != "meeting":
        parser.error("Finite mandate cases use meeting mode.")
    if (args.prioritize_exclusions or args.prioritize_exclusions_after_rejection) and case.get("mandate_game") is None:
        parser.error("Exclusion instructions require a finite mandate case.")
    Mandates.from_case(case, countries)

    settings = dict(model=args.model, started=datetime.now(timezone.utc).isoformat(),
                    case=case, countries=countries, mode=args.mode, turn_cap=args.turn_cap, vote=args.vote,
                    call_timeout=args.call_timeout)
    if seat_models:
        settings["seat_models"] = seat_models
    if args.call_cap is not None:
        settings["call_cap"] = args.call_cap
    for key in ("prioritize_exclusions", "prioritize_exclusions_after_rejection"):
        if getattr(args, key):
            settings[key] = True
    previous = None
    source = args.extend_from or args.resume_from
    if source:
        old = json.loads((source / "settings.json").read_text())
        for key in ("model", "case", "countries", "mode"):
            if old[key] != settings[key]:
                parser.error(f"Cannot continue with a different {key}.")
        if old.get("seat_models", {}) != seat_models:
            parser.error("Cannot continue with different seat models.")
        if any(old.get(key, False) != settings.get(key, False)
               for key in ("prioritize_exclusions", "prioritize_exclusions_after_rejection")):
            parser.error("Cannot continue with different exclusion instructions.")
        if args.extend_from:
            result = verify_run(source, simulate)
            previous_limits = {"turn_cap": old["turn_cap"], "call_cap": old.get("call_cap")}
            limits = {"turn_cap": args.turn_cap, "call_cap": args.call_cap}
            exhausted = result.get("status")
            shrank_limit = any(
                (limit is None) != (previous_limits[name] is None)
                or (limit is not None and limit < previous_limits[name])
                for name, limit in limits.items()
            )
            if (exhausted not in limits or shrank_limit
                    or limits[exhausted] <= previous_limits[exhausted]):
                parser.error("Increase the exhausted budget and preserve the other limit when extending a meeting.")
            previous = Recording(source, stop_before_schema=BALLOT)
            settings["extended_from"] = str(source)
        else:
            if (source / "result.json").exists() or any(
                old.get(k) != settings.get(k) for k in ("turn_cap", "call_cap", "vote")
            ):
                parser.error("Resume an unfinished run with the same budgets and vote setting.")
            previous = Recording(source)
            settings["resumed_from"] = str(source)
    actors = ("analyst",) if args.mode == "solo" else countries
    models = dict.fromkeys(seat_models.get(actor, args.model) for actor in actors)
    runners = {model: CodexRunner(model, args.codex, args.call_timeout) for model in models}
    settings["codex"] = next(iter(runners.values())).executable
    args.out.mkdir(parents=True, exist_ok=False)
    (args.out / "settings.json").write_text(pretty(settings) + "\n")
    with (args.out / "calls.jsonl").open("x") as log:
        def record(item):
            log.write(json.dumps(item, ensure_ascii=False) + "\n")
            log.flush()

        def call(country, prompt, schema):
            request = decision_request(settings, country, prompt, schema)
            record(request)
            answer = previous.take(request) if previous else None
            reused = answer is not None
            if not reused:
                answer = runners[seat_models.get(country, args.model)](prompt, schema)
            record(dict(event="response", country=country, answer=answer, reused=reused))
            return answer

        try:
            result = simulate(case, countries, args.mode, args.turn_cap, args.vote, call, args.call_cap,
                              prioritize_exclusions=args.prioritize_exclusions,
                              prioritize_exclusions_after_rejection=args.prioritize_exclusions_after_rejection)
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
