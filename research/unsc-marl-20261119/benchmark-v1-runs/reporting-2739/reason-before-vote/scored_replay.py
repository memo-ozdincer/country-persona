"""Load the exact prior docket evaluators by path to avoid module shadowing."""
import argparse
import json
from unittest.mock import patch

from experiment import HERE, PRIOR, previous

scorer = previous.load("prior_2739_score", PRIOR / "score.py")
routing = previous.load("prior_2739_routing", PRIOR / "routing.py")


def evaluate(mode):
    if mode == "score":
        with patch.object(scorer, "HERE", HERE):
            return scorer.score()
    with patch.object(routing, "HERE", HERE):
        return routing.run()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("score", "routing"))
    print(json.dumps(evaluate(parser.parse_args().mode), ensure_ascii=False, indent=2))
