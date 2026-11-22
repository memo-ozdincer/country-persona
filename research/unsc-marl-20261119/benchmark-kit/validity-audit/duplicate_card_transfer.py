"""Run the frozen modular writing procedure on a new Council docket."""
import argparse
import json
from pathlib import Path
from unittest.mock import patch

import duplicate_card_modular as original
from duplicate_card_records import FIT
import source_record_run as runner

CASE = Path(__file__).with_name("source-record-dprk-routing.json")
SKEW = ((.10, .60, .10, .20), (.10, .10, .60, .20))


def suite():
    case = json.loads(CASE.read_text())
    public = ("Write the public portion of a compact historical Council record in at most 85 words. "
              "Give the draft symbol, sponsor, numeric tally and the reason it failed. State the proposed "
              "Panel renewal, independence and reporting. Distinguish the Panel mandate, Committee and "
              "sanctions. State what proposed terms took effect and give a short labeled analytical suggestion. "
              "Use only the four supplied evidence IDs in brackets. Omit headings and repetitions.")
    groups = [("public", case["public"], public, original.PUBLIC_CAP)]
    for name, card in case["cards"].items():
        task = (f"In one short sentence or two, {card['prompt']} Cite [{name}]. "
                "Use at most 28 words. Use only the supplied passage.")
        groups.append((name, {name: card["text"]}, task, original.CARD_CAP))
    for name, evidence, task, cap in groups:
        yield {"id": f"{case['family']}/{name}/component", "evidence_ids": list(evidence), "seen": [], "cap": cap,
               "messages": [
                   {"role": "system", "content": "You write internal historical Council records. The supplied historical excerpts are the only factual authority."},
                   {"role": "user", "content": json.dumps({"task": task, "evidence": evidence}, ensure_ascii=False)},
               ]}


def locks():
    return {**original.locks(), **{f"validity-audit/{p.name}": runner.digest(p)
                                   for p in (CASE, Path(__file__))}}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("check", "run", "replay"))
    parser.add_argument("directory", type=Path, nargs="?")
    parser.add_argument("--model", type=Path)
    args = parser.parse_args()
    if args.mode == "check":
        print(json.dumps({"suite": list(suite()), "sha256": locks(), "frozen_routing_sha256": runner.digest(FIT),
                          "new_inventory_marginals": SKEW}, indent=2, ensure_ascii=False))
    elif args.directory is None:
        parser.error("directory is required")
    else:
        with patch.object(original, "suite", suite):
            if args.mode == "run":
                if args.model is None:
                    parser.error("--model is required")
                with patch.multiple(runner, locks=locks, episode=original.episode):
                    runner.run(args.model, args.directory)
            else:
                # Capture the unpatched lock function while reusing the exact token verifier.
                expected = locks()
                with patch.object(original, "locks", return_value=expected):
                    print(json.dumps(original.replay(args.directory), indent=2))
