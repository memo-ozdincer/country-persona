"""Generate actual disclosures from a mixed team on two new workshop domains."""
import argparse
import json
from pathlib import Path
from unittest.mock import patch

import numpy as np

import warrant_requester_blend as receiver
import warrant_live as phrases
import warrant_live_authorized as authorized

design = receiver.design
world = receiver.world
HERE = world.HERE
EVIDENCE = HERE / "warrant-language-team-evidence"
FAMILY = "warrant-language-team"
DOMAIN_SEED = 170823
STYLE = (
    "If any grade is zero, choose the first zero-grade package in A, B, C order. Otherwise choose the package with the highest grade, breaking ties in A, B, C order.",
    "Choose the package with the highest grade, breaking ties in A, B, C order.",
)
SYSTEM = (
    "File a single grade from your private workshop card. Select its package using the disclosure convention. "
    "Use exactly the format {delegate} reports grade {grade} for {package}. Insert the delegate's ID and the "
    "chosen package and its grade. Output only that line with its period. No other grade, reasoning or text."
)


def orbit(cards):
    return {tuple(tuple(sorted(map(tuple, side[:, order]))) for side in cards)
            for order in world.two.ORDERINGS}


def domains():
    rng = np.random.default_rng(DOMAIN_SEED)
    seen = set.union(*(orbit(profile) for profile in world.domains()))
    for _ in range(2):
        values = np.array([rng.choice(64, 4, replace=False) for _ in range(3)])
        cards = np.stack((values // 16, values // 4 % 4, values % 4), axis=-1)
        signature = orbit(cards)
        assert not signature & seen
        seen.update(signature)
        yield cards


def fitted(task):
    weights = np.asarray(json.loads(design.PREVIOUS.read_text())["fitted_weights"])
    return design.partners(task, world.prior(False), weights)


def requests():
    for index, cards in enumerate(domains()):
        selected = fitted(world.Workshop(cards))["fitted"]
        for role, card_type in np.ndindex(3, 4):
            key = f"d{index}/D{role+1}/card{card_type}"
            card = cards[role, card_type]
            if role < 2:
                payload = {"delegate": f"D{role+1}", "private_grades": dict(zip(world.two.PACKAGES, card.tolist())),
                           "disclosure_convention": STYLE[role]}
                yield phrases.prompt(key, 25, SYSTEM, payload)
            else:
                slot = selected[role, card_type]
                yield authorized.note(key, (role, int(slot), int(card[slot])), cards[:, card_type])


def episode(generate):
    incoming = list(requests())
    rows = {}
    for start in range(0, len(incoming), 8):
        rows.update(generate(incoming[start:start + 8]))
    return [{"family": FAMILY, "final": rows}]


def pins():
    files = (Path(__file__).resolve(), EVIDENCE / "protocol.md", design.PREVIOUS, Path(world.__file__),
             Path(receiver.__file__), Path(receiver.flexible.__file__), Path(receiver.adapt.__file__),
             Path(design.__file__), Path(phrases.__file__), Path(authorized.__file__), Path(phrases.runner.__file__))
    return {str(p.relative_to(HERE)): phrases.runner.digest(p) for p in files}


def verify(folder):
    from transformers import AutoTokenizer

    launch = json.loads((folder / "launch.json").read_text())
    complete = json.loads((folder / "complete.json").read_text())
    transcript = folder / "transcript.jsonl"
    finals = folder / "final-records.json"
    assert launch["sha256"] == pins() and complete["transcript_sha256"] == phrases.runner.digest(transcript)
    assert complete["final_records_sha256"] == phrases.runner.digest(finals)
    rows = {row["id"]: row for row in map(json.loads, transcript.read_text().splitlines())}
    prompts = list(requests())
    assert rows.keys() == {p["id"] for p in prompts} and len(rows) == complete["records"] == 24
    token = AutoTokenizer.from_pretrained(launch["model"], local_files_only=True)
    eos = token.convert_tokens_to_ids("<|im_end|>")
    for prompt in prompts:
        row = rows[prompt["id"]]
        assert all(row[k] == v for k, v in prompt.items()) and row["input_ids"] == phrases.runner.encode(token, prompt)
        ids = row["output_ids"]
        assert 0 < len(ids) <= row["cap"] and eos not in ids[:-1]
        assert row["ended"] == (ids[-1] == eos)
        assert row["output"] == token.decode(ids, skip_special_tokens=True).strip()
    assert json.loads(finals.read_text()) == {FAMILY: {key: row["output"] for key, row in rows.items()}}
    return rows


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("mode", choices=("run", "verify"))
    cli.add_argument("folder", type=Path)
    cli.add_argument("--model", type=Path)
    args = cli.parse_args()
    if args.mode == "run":
        assert len(list(requests())) == 24
        with patch.multiple(phrases.runner, episode=episode, locks=pins):
            phrases.runner.run(args.model, args.folder)
    else:
        print({"verified_generations": len(verify(args.folder))})
