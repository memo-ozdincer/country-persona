"""Follow frozen routing actions through the protected writer on Resolution 2719."""
import json
from pathlib import Path
import sys
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
KIT = HERE.parent
sys.path.insert(0, str(KIT.parent / "validity-audit"))
import source_record_run as runner

PROTOCOL = HERE / "protocol.json"
PACKET = KIT / "facilitator-resolution-2719-evidence/packet.json"
FIT = KIT / "facilitator-passage-adaptive-fit-evidence/results.json"
CRITIC = KIT / "facilitator-passage-responder-critic-evidence/results.json"
REPLIES = KIT / "facilitator-measured-channel-evidence/final-records.json"
POOLED = KIT / "facilitator-resolution-2719-evidence/final-records.json"
MODEL = Path("/mfs1/u/memo/country-persona-research/models/Qwen3.5-4B/851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a")
EVIDENCE = HERE / "evidence"
FAMILY = "live-2719-routing-transfer"


def load(path):
    return json.loads(path.read_text())


def plan():
    config = load(PROTOCOL)
    prior = config["inventory_law"]
    left, right, ask, reply = load(FIT)["cases"]["2719"][prior][config["fit"]]["team"]
    declared = load(CRITIC)["passage_cases"]["2719"][prior]["fitted_opening"]["policies"]["declared"]["questions"]
    cards = load(PACKET)["cards"]
    speeches, = load(REPLIES).values()
    pooled, = load(POOLED).values()

    def note(source, text):
        return {"desk": cards[source - 1]["speaker"], "text": text}

    def prompt(key, notes, supplement):
        return {"id": key, "cap": config["caps"]["body_tokens"],
                "messages": [{"role": "system", "content": config["instruction"]},
                             {"role": "user", "content": json.dumps({"notes": notes, "supplement": supplement},
                                                                  ensure_ascii=False)}]}

    paths, prompts = {}, {}
    for world, (l, r) in config["worlds"].items():
        a, b = left[l], right[r]
        assert a > 0 and b > 0 and a != b
        assert l & (1 << (a - 1)) and r & (1 << (b - 1))
        mask = (1 << (a - 1)) | (1 << (b - 1))
        notes = [note(source, speeches[f"0/{source}"]) for source in (a, b)]
        controls = {"learned": (ask[mask], reply[r][b][ask[mask]]),
                    "declared": (declared[mask], reply[r][b][declared[mask]]),
                    "silence": (0, reply[r][b][0])}
        if world == "change_source":
            controls["fixed_france"] = (0, 3)
            assert controls["learned"][1] != controls["silence"][1]
        else:
            assert controls["learned"][1] == controls["silence"][1]
            assert controls["learned"][0] != controls["silence"][0]
        paths[world] = {}
        for arm, (query, source) in controls.items():
            assert source == 0 or r & (1 << (source - 1))
            slot = f"{query}/{source}" if source else None
            payload = note(source, speeches[slot]) if slot else None
            candidate = prompt(f"{world}/{arm}", notes, payload)
            existing = next((key for key, p in prompts.items() if p["messages"] == candidate["messages"]), None)
            key = existing or candidate["id"]
            prompts[key] = prompts.get(key, candidate)
            paths[world][arm] = {"receipt": mask, "opening_sources": [a, b], "query": query,
                                 "reply_source": source, "archived_reply": slot, "generation": key}
    key = "pooled"
    prompts[key] = prompt(key, [note(i + 1, pooled[f"solo/{i}"]) for i in range(3)], None)
    return list(prompts.values()), paths


def pins():
    files = (Path(__file__), PROTOCOL, PACKET, FIT, CRITIC, REPLIES, POOLED, Path(runner.__file__))
    return {str(p.relative_to(KIT)) if p.is_relative_to(KIT) else p.name: runner.digest(p) for p in files}


def episode(generate):
    prompts, _ = plan()
    return [{"family": FAMILY, "final": generate(prompts)}]


if __name__ == "__main__":
    prompts, paths = plan()
    (HERE / "frozen-actions.json").write_text(json.dumps(paths, indent=2) + "\n")
    print(json.dumps(paths), flush=True)
    with patch.multiple(runner, episode=episode, locks=pins):
        runner.run(MODEL, EVIDENCE)
