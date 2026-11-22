"""Probe whether anonymous evidence passages satisfy the two routing roles."""
import argparse
from contextlib import contextmanager
from hashlib import sha256
from itertools import product
import json
from pathlib import Path
from unittest.mock import patch

from duplicate_card_language import CASES, POLICY, scorer

# The required claim types are not visible in the passage headers. Each near
# miss preserves the speaker while withholding or changing a material fact.
REQUIRED = {
    "venezuela": (
        "Ndong Mba announced the results as Council President. Equatorial Guinea abstained on "
        "S/2019/186 and voted for S/2019/190.",
        "Indonesia abstained on both drafts, called for inclusive political dialogue, and asked "
        "all parties to accept the Secretary-General's good offices.",
    ),
    "dprk": (
        "Yamazaki spoke in his national capacity as Japan's representative and said Russia's veto "
        "forced the Panel of Experts to end operations.",
        "China abstained, saying Russia's views were not taken on board and time remained for "
        "consultations. It supported independent Panel work, a sanctions time limit and periodic reviews.",
    ),
}
REMOVALS = {
    "venezuela": (" Equatorial Guinea itself abstained on S/2019/186 and voted for S/2019/190.",
                  " and called on all parties to accept the Secretary-General's good offices"),
    "dprk": (" in his national capacity as Japan’s representative", " and consultation time remained"),
}
# Author-supplied counterfactuals, never released as historical evidence.
REVERSALS = {
    "venezuela": (("abstained on S/2019/186", "voted for S/2019/186"),
                  ("accept the Secretary-General's good offices", "reject the Secretary-General's good offices")),
    "dprk": (("in his national capacity as Japan’s representative", "solely in his capacity as Council President"),
             ("consultation time remained", "there was no time left for consultations")),
}
ORDERS = ((1, 2, 0), (2, 0, 1), (0, 1, 2))
SYSTEM = (
    "Classify the single passage for a historical records desk. A passage qualifies only if "
    "it explicitly supports all parts of one listed evidence requirement. Missing or contradicted "
    "parts mean it does not qualify. Do not rely on outside knowledge. Return just the choice letter."
)


def entries():
    for case, path in CASES.items():
        cards = json.loads(path.read_text())["cards"]
        for offset, entry in enumerate(cards.values()):
            text = entry["text"]
            first, remainder = text.split(". ", maxsplit=1)
            removed = REMOVALS[case][offset]
            original, replacement = REVERSALS[case][offset]
            assert text.count(original) == text.count(removed) == 1
            for variant, passage in (
                ("full", text), ("reordered", f"{remainder} {first}."),
                ("missing", text.replace(removed, "", 1)),
                ("reversed", text.replace(original, replacement, 1)),
            ):
                yield case, offset + 1, variant, passage, offset + 1 if variant in ("full", "reordered") else 0


def observations():
    for case, intended, variant, text, _ in entries():
        tasks = {0: "The passage supports neither full requirement.",
                 **{i: requirement for i, requirement in enumerate(REQUIRED[case], 1)}}
        for rotation, order in enumerate(ORDERS):
            content = {"passage": text,
                       "choices": {label: tasks[k] for label, k in zip("ABC", order, strict=True)}}
            yield {"observation": (case, intended, variant, rotation), "legal": order,
                   "messages": [{"role": "system", "content": SYSTEM},
                                {"role": "user", "content": json.dumps(content, ensure_ascii=False)}]}


def hashes():
    paths = (Path(__file__), Path(scorer.__file__), POLICY, *CASES.values())
    root = Path(__file__).resolve().parents[2]
    return {str(p.resolve().relative_to(root)): sha256(p.read_bytes()).hexdigest() for p in paths}


@contextmanager
def inputs():
    with patch.multiple(scorer, observations=observations, hashes=hashes):
        yield


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("check", "run"))
    parser.add_argument("directory", type=Path, nargs="?")
    parser.add_argument("--model", type=Path)
    args = parser.parse_args()
    if args.mode == "check":
        print(json.dumps({"prompts": list(observations()), "key": list(entries()), "sha256": hashes()},
                         indent=2, ensure_ascii=False))
    else:
        if args.directory is None or args.model is None:
            parser.error("run requires directory and --model")
        with inputs():
            scorer.score(args.model, args.directory)
