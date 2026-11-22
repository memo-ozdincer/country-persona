"""Test frozen Qwen desks executing the fitted buffered signaling protocol."""
import argparse
from contextlib import contextmanager
from hashlib import sha256
from itertools import product
import json
from pathlib import Path
import sys
from unittest.mock import patch

from duplicate_card_outcome_policy import EVIDENCE
from duplicate_card_routes import CASE as VENEZUELA
from duplicate_card_transfer import CASE as DPRK
from source_route_search import LEGAL

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))
import relay_text as scorer
sys.path.pop(0)

POLICY = EVIDENCE / "buffered-fit.json"
CASES = {"venezuela": VENEZUELA, "dprk": DPRK}
SYSTEM = (
    "Act as a dispatch desk handling a historical Council record. Follow your dispatch policy. "
    "Use only your listed cards and the signal you actually received. Return only the letter of an action."
)
SIGNAL_RULE = (
    "Announce if you hold card 2 alone. Otherwise pass.",
    "Announce if you hold card 2, whether alone or with card 1. Otherwise pass.",
)
DELIVERY_RULE = (
    "With card 1 alone send card 1. With card 2 alone send card 2 only if you announced. "
    "If you hold both and did not announce, send card 1 when a peer announcement arrived, otherwise send card 2. "
    "If you hold both and announced, pass. If no rule applies, pass.",
    "With card 1 alone send card 1. With card 2 alone, send card 2 only if you announced and no peer announcement arrived. "
    "If you hold both and announced, send card 1 when a peer announcement arrived, otherwise send card 2. "
    "If you hold both and did not announce, pass. If no rule applies, pass.",
)


def observations():
    table = json.loads(POLICY.read_text())["trained_tables"]["matched"]
    for name, path in CASES.items():
        case = json.loads(path.read_text())
        cards = (list(case["cards"].values()))
        for seat, inventory in product(range(2), range(4)):
            local = {f"card {i+1}": card["text"] for i, card in enumerate(cards) if inventory & (1 << i)}
            context = {"case": case["family"], "desk": seat + 1, "held_cards": local}
            yield {"observation": (name, "signal", seat, inventory, 0, 0),
                   "legal": (0, 1), "messages": [
                       {"role": "system", "content": SYSTEM},
                       {"role": "user", "content": json.dumps({**context, "policy": SIGNAL_RULE[seat],
                           "choices": {"A": "pass", "B": "announce availability"}}, ensure_ascii=False)}]}
            for own, peer in product(range(2 if inventory & 2 else 1), range(2)):
                expected = table[seat][inventory][1 + 2 * own + peer]
                assert LEGAL[inventory, expected]
                body = {**context, "you_announced": bool(own), "peer_announcement_received": bool(peer),
                        "policy": DELIVERY_RULE[seat],
                        "choices": {"A": "pass", "B": "send card 1", "C": "send card 2"}}
                yield {"observation": (name, "delivery", seat, inventory, own, peer),
                       "legal": (0, 1, 2), "messages": [
                           {"role": "system", "content": SYSTEM},
                           {"role": "user", "content": json.dumps(body, ensure_ascii=False)}]}


def hashes():
    paths = (Path(__file__), Path(scorer.__file__), POLICY, *CASES.values())
    return {str(p.relative_to(HERE.parents[1])): sha256(p.read_bytes()).hexdigest() for p in paths}


@contextmanager
def inputs():
    with patch.multiple(scorer, observations=observations, hashes=hashes):
        yield


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("mode", choices=("check", "run"))
    cli.add_argument("directory", type=Path, nargs="?")
    cli.add_argument("--model", type=Path)
    args = cli.parse_args()
    if args.mode == "check":
        print(json.dumps({"prompts": list(observations()), "sha256": hashes()}, indent=2, ensure_ascii=False))
    else:
        if args.directory is None or args.model is None:
            cli.error("run requires directory and model")
        with inputs():
            scorer.score(args.model, args.directory)
