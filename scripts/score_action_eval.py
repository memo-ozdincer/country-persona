"""Score immutable vote cases against separately stored references and actual outputs."""
import argparse
from country_persona.action_eval import score_actions
from country_persona.io import read_jsonl, write_json

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", required=True)
    parser.add_argument("--references", required=True)
    parser.add_argument("--predictions", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    report = score_actions(list(read_jsonl(args.cases)), list(read_jsonl(args.references)), list(read_jsonl(args.predictions)))
    write_json(args.output, report)
    print(report["overall"])
