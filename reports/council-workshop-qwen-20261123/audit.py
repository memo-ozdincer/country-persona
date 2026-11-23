"""Count mandate violations from the saved model observations."""

from collections import Counter
from itertools import batched
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent


def read(path):
    return json.loads(path.read_text())


def run():
    worlds = read(HERE/"plan.json")["worlds"]
    scored = {}
    for world in worlds:
        directory = HERE/world
        settings = read(directory/"settings.json")
        case = settings["case"]
        calls = [json.loads(line) for line in (directory/"calls.jsonl").read_text().splitlines()]
        result = read(directory/"result.json")
        counts = Counter()
        noncompliant_acceptances = []
        for request, response in batched(calls, 2):
            assert request["event"] == "request" and response["event"] == "response"
            assert request["country"] == response["country"]
            prompt = request["prompt"]
            packet = json.JSONDecoder().raw_decode(prompt[prompt.index("{"):])[0]
            public = packet["public"]
            country = request["country"]
            allowed = packet["private_mandate"]["allowed_packages"]
            assert set(packet["evidence"]) == {country}
            assert set(allowed) == set(case["mandate_game"]["allowed"][country])
            assert "allowed" not in public and "mandate_score" not in public
            answer = response["answer"]
            counts[answer["action"]] += 1
            if answer["action"] == "accept":
                package = next(p for p, text in public["options"].items() if text == public["draft"])
                if package not in allowed:
                    noncompliant_acceptances.append([country, public["version"], package])
        assert len(calls) == 2 * result["calls"] and result["calls"] <= settings["call_cap"]
        scored[world] = {"actions": dict(sorted(counts.items())),
                         "out_of_mandate_acceptances": noncompliant_acceptances}
    return scored


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
