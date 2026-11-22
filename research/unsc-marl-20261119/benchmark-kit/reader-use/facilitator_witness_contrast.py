"""Test paired claim scope with the source and the exact witness held fixed."""
import argparse
import json
from pathlib import Path
from unittest.mock import patch

import facilitator_scope_check as earlier

HERE = earlier.HERE
PACK = HERE / "facilitator-witness-contrast-packet.json"
FAMILY = "facilitator-witness-contrast"
CAP = 100
ARMS = ("direct", "compare_first")
DIRECT = earlier.TASK
COMPARE = (
    "Decide whether the cited words rule out the assertion. Use the card to resolve references in the quote. "
    "Compare the assertion and cited words on speaker, act, exact target, and strength or condition. "
    "If the quote concerns a different vote, version, policy mechanism, or degree, ask if both statements "
    "can be true. State one concrete way they can coexist or the two incompatible positions. "
    "An abstention and nonparticipation are different roll-call acts. An opinion and a vote can coexist. "
    "Classify only what the cited words establish. Return one line containing your explanation in at most "
    "25 words, a vertical bar, and one verdict word: open if both can be true, conflict if they cannot."
)


def cases():
    data = earlier.base.load(PACK)
    for family, data in data.items():
        for item in data["anchors"]:
            assert item["card"].count(item["witness"]) == 1
            for expected in ("open", "conflict"):
                payload = {"assertion": item[expected], "cited_words": item["witness"], "official_card": item["card"]}
                yield f"{family}/{item['id']}/{expected}", expected, payload


def requests():
    for key, _, payload in cases():
        for arm, prompt in zip(ARMS, (DIRECT, COMPARE), strict=True):
            yield earlier.quote.held.prompt(f"{key}/{arm}", CAP, prompt, payload)


def episode(generate):
    wanted = list(requests())
    result = {}
    for start in range(0, len(wanted), 8):
        result.update(generate(wanted[start:start + 8]))
    return [{"family": FAMILY, "final": result}]


def pins():
    locks = earlier.pins()
    for p in (Path(__file__), PACK):
        locks[str(p.resolve().relative_to(HERE.parents[1]))] = earlier.runner.digest(p)
    return locks


def verify(directory):
    locked = pins()
    with patch.multiple(earlier.base, pins=lambda: locked, requests=requests, CAP=CAP, FAMILY=FAMILY):
        return earlier.base.rows(directory)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode", choices=("run", "verify"))
    p.add_argument("directory", type=Path)
    p.add_argument("--model", type=Path)
    args = p.parse_args()
    if args.mode == "run":
        with patch.multiple(earlier.runner, episode=episode, locks=pins):
            earlier.runner.run(args.model, args.directory)
    else:
        print(json.dumps({"verified_generations": len(verify(args.directory))}))
