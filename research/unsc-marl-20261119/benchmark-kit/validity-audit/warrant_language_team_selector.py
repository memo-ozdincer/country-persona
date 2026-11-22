"""Select a package with a language model and forward its grade from the private card."""
import argparse
import json
from pathlib import Path
from unittest.mock import patch

import warrant_language_team as base
import warrant_language_team_score as scorer
import warrant_reasons as replay

EVIDENCE = base.EVIDENCE / "package-only"
FAMILY = "warrant-language-team-selector"
SYSTEM = (
    "Select exactly one package from your own private workshop card. Follow the disclosure convention. "
    "Return only the letter A, B, or C. The sender will look up the selected package's numeric grade. "
    "Return no grade, words or punctuation."
)


def requests():
    for query in base.requests():
        if "/D3/" in query["id"]:
            continue
        private = json.loads(query["messages"][-1]["content"])
        yield base.phrases.prompt(query["id"], 8, SYSTEM, private)


def episode(generate):
    return [{"family": FAMILY, "final": generate(list(requests()))}]


def pins():
    files = (Path(__file__).resolve(), EVIDENCE / "protocol.md", base.EVIDENCE / "complete.json",
             base.EVIDENCE / "transcript.jsonl", Path(replay.__file__))
    return {**base.pins(), **{str(path.relative_to(base.HERE)): base.phrases.runner.digest(path) for path in files}}


def verified(folder):
    with patch.multiple(replay, requests=requests, pins=pins, FAMILY=FAMILY):
        return replay.verify(folder)


def run(folder):
    selected = verified(folder)
    copied = base.verify(base.EVIDENCE)
    views = {key: row for key, row in copied.items() if "/D3/" in key}
    source_link = {}
    for i, cards in enumerate(base.domains()):
        for role in range(2):
            for typ in range(4):
                key = f"d{i}/D{role+1}/card{typ}"
                row = selected[key]
                letter = row["output"]
                if row["ended"] and letter in scorer.PACKAGES:
                    slot = scorer.PACKAGES.index(letter)
                    line = base.phrases.wire(role, slot, int(cards[role, typ, slot]))
                else:
                    line = ""
                views[key] = {**row, "output": line}
                source_link[key] = {"model_package_output": letter, "sender_compiled_line": line}
    return {"selection_and_compilation": source_link, "reused_exact_D3_reports": len(copied) - len(selected),
            "replay": scorer.run(views)}


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("mode", choices=("run", "verify", "score"))
    cli.add_argument("folder", type=Path)
    cli.add_argument("--model", type=Path)
    args = cli.parse_args()
    if args.mode == "run":
        assert len(list(requests())) == 16
        with patch.multiple(base.phrases.runner, episode=episode, locks=pins):
            base.phrases.runner.run(args.model, args.folder)
    elif args.mode == "verify":
        print({"verified_generations": len(verified(args.folder))})
    else:
        print(json.dumps(run(args.folder), ensure_ascii=False, indent=2))
