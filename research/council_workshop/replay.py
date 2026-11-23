"""Replay a saved run offline and verify each model input and final result."""
import argparse
from pathlib import Path

from recording import verify_run
from run import simulate


def replay(directory):
    return verify_run(directory, simulate)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    directory = parser.parse_args().directory
    replay(directory)
    print(f"{directory}: replay verified")
