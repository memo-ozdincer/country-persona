"""Render the frozen Resolution 2466 routes and compare exact evidence selections."""
from itertools import product
import json
from pathlib import Path
import sys
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent / "validity-audit"))
import source_record_run as runner

PACKET = HERE / "packet.json"
FORECAST = HERE / "forecast.json"
EVIDENCE = HERE / "evidence"
FAMILY = "haiti2466-budget-transfer"
MODEL = Path("/mfs1/u/memo/country-persona-research/models/Qwen3.5-4B/851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a")
INSTRUCTION = (
    "Write only a supplementary Council record in at most 70 words. A verified account of the actual decision "
    "and vote will be appended separately. Report the positions and reasons in the attributed evidence. "
    "Distinguish what each delegation said from what the Council decided. Keep concrete qualifications and "
    "separate reasons with their correct speaker. Do not infer missing facts from the headings. Output prose only."
)


def read(path):
    return json.loads(path.read_text())


def variants(packet, receipt, cap):
    cards = packet["cards"]
    atoms = [(slot, atom) for slot, card in enumerate(cards) if receipt & (1 << slot) for atom in card["atoms"]]
    options = []
    for selected in product((0, 1), repeat=len(atoms)):
        used = [(i, a) for take, (i, a) in zip(selected, atoms, strict=True) if take]
        ids = {a["id"] for _, a in used}
        groups = [{"desk": card["desk"], "statements": [a["text"] for i, a in used if i == slot]}
                  for slot, card in enumerate(cards) if any(i == slot for i, _ in used)]
        cost = sum(len(group["desk"].split()) + sum(len(s.split()) for s in group["statements"]) for group in groups)
        value = sum(a["points"] for _, a in used) + (
            packet["joint"]["points"] if set(packet["joint"]["needs"]) <= ids else 0
        )
        options.append((value, -cost, tuple(sorted(ids)), groups))
    return {name: {"points": value, "words": -cost, "ids": ids, "evidence": groups}
            for name, (value, cost, ids, groups) in {
                "selected": max((r for r in options if -r[1] <= cap), key=lambda r: r[:3]),
                "all": options[-1],
            }.items()}


def prompts():
    packet, forecast = read(PACKET), read(FORECAST)
    assert runner.digest(PACKET) == forecast["sha256"][PACKET.name]
    sources = {7}
    paths = {}
    for key, world in forecast["worlds"].items():
        paths[key] = {}
        for arm, (question, reply) in world["tail"].items():
            received = world["receipt"] | (1 << (reply - 1) if reply else 0)
            sources.add(received)
            paths[key][arm] = {"question": question, "reply": reply, "received": received,
                               "selected": f"{received}/selected", "all": f"{received}/all"}
    rows, catalog = [], {}
    for received in sorted(sources):
        for name, item in variants(packet, received, 70).items():
            key = f"{received}/{name}"
            rows.append({"id": key, "cap": 170, "messages": [
                {"role": "system", "content": INSTRUCTION},
                {"role": "user", "content": json.dumps(item["evidence"], ensure_ascii=False)},
            ]})
            catalog[key] = {k: v for k, v in item.items() if k != "evidence"}
            if name == "selected":
                predicted = forecast["curves"]["70"]["prefix"][received] - packet["base_points"]
                assert item["points"] == predicted
    assert len(rows) == 4
    return rows, {"paths": paths, "catalog": catalog, "pooled": "7/all"}


def episode(generate):
    rows, _ = prompts()
    return [{"family": FAMILY, "final": generate(rows)}]


def pins():
    files = (Path(__file__), PACKET, FORECAST, HERE / "protocol.md", HERE / "generation-protocol.md",
             Path(runner.__file__))
    return {p.name: runner.digest(p) for p in files}


if __name__ == "__main__":
    _, paths = prompts()
    (HERE / "generation-paths.json").write_text(json.dumps(paths,ensure_ascii=False,indent=2)+"\n")
    with patch.multiple(runner, episode=episode, locks=pins):
        runner.run(MODEL, EVIDENCE)
