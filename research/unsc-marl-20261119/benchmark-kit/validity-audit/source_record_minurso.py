"""Run the Western Sahara record comparison using the frozen source-record runner."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
from unittest.mock import patch

import source_record_episode as scenario
import source_record_run as runner

PACK = Path(__file__).with_name("source-record-minurso.json")
JUDGE = PACK.parents[2] / "judge/instructions.md"


def locks():
    inputs = (Path(__file__), PACK, Path(scenario.__file__), Path(runner.__file__), JUDGE)
    return {path.name: sha256(path.read_bytes()).hexdigest() for path in inputs}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("check", "run"))
    parser.add_argument("--model", type=Path)
    parser.add_argument("--directory", type=Path)
    args = parser.parse_args()
    with patch.object(scenario, "PACK", PACK), patch.object(runner, "locks", locks):
        if args.mode == "check":
            print(json.dumps({**scenario.dry(), "sha256": locks()}, indent=2))
        elif args.model is None or args.directory is None:
            parser.error("run requires --model and --directory")
        else:
            runner.run(args.model, args.directory)


if __name__ == "__main__":
    main()
