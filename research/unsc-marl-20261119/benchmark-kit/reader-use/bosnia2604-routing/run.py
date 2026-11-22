"""Frozen CPU comparison of adaptive routing, fixed-source drafts and pooled solo."""
import json
from pathlib import Path
import re
import sys
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent / "validity-audit"))
import source_record_run as runner

PROTOCOL = HERE / "protocol.json"
MODEL = Path("/mfs1/u/memo/country-persona-research/models/Qwen3.5-4B/851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a")
ARMS = ("adaptive", "fixed_uk", "fixed_russia", "solo")


def choose(protocol, notes):
    missing = [row for row in protocol["questions"]
               if not all(re.search(pattern, notes[row["desk"]], re.I) for pattern in row["patterns"])]
    return max(missing, key=lambda row: row["weight"], default=None)


def episode(generate):
    protocol = json.loads(PROTOCOL.read_text())
    public, desks = protocol["public"], protocol["desks"]
    rows = {}

    def batch(stage, requests):
        stage_instructions = protocol[f"{stage}_instruction"]
        data = [{"id": key, "cap": protocol["caps"][stage],
                 "messages": [{"role": "system", "content": stage_instructions},
                              {"role": "user", "content": json.dumps(payload, ensure_ascii=False)}]}
                for key, payload in requests]
        rows.update(generate(data))

    names = list(desks)
    batch("opening", [(f"{mode}/{i}", {"assigned": desk, **({"source": desks[desk]} if mode == "local"
                                                            else {"sources": desks})})
                      for mode in ("local", "pooled") for i, desk in enumerate(names)])
    notes = {desk: rows[f"local/{i}"]["output"] for i, desk in enumerate(names)}
    solo_notes = {desk: rows[f"pooled/{i}"]["output"] for i, desk in enumerate(names)}
    question = choose(protocol, notes)
    neutral = protocol["neutral_request"]
    followups = [(f"{arm}/followup", {"assigned": desk, "source": desks[desk], "request": neutral})
                 for arm, desk in zip(ARMS[1:3], names, strict=True)]
    followups.append(("solo/followup", {"assigned": "pooled editor", "sources": desks, "request": neutral}))
    followups.append(("adaptive/followup", {
        "assigned": question["desk"] if question else "editorial placeholder",
        "source": desks[question["desk"]] if question else "",
        "prior_notes": notes,
        "request": question["request"] if question else "No additional evidence requested. Output SKIP.",
    }))
    batch("followup", followups)
    owners = {"adaptive": question["desk"] if question else "none",
              "fixed_uk": names[0], "fixed_russia": names[1], "solo": "pooled editor"}
    batch("final", [(f"{arm}/final", {"public_record": public,
                                   "notes": solo_notes if arm == "solo" else notes,
                                   "supplement": {"owner": owners[arm],
                                                  "note": rows[f"{arm}/followup"]["output"]
                                                  if arm != "adaptive" or question else ""}})
                    for arm in ARMS])
    return [{"family": "bosnia2604-routing", "final": {k: rows[k] for k in (f"{a}/final" for a in ARMS)}}]


def pins():
    return {p.name: runner.digest(p) for p in (PROTOCOL, Path(__file__), Path(runner.__file__))}


if __name__ == "__main__":
    with patch.multiple(runner, episode=episode, locks=pins):
        runner.run(MODEL, HERE / "evidence")
