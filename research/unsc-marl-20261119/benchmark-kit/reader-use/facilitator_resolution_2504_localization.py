"""Check whether a judge citation uniquely reaches the changed characters."""
import argparse
from difflib import SequenceMatcher
import json

import facilitator_resolution_2504_judge as study


def locate(item, verdict):
    if verdict["decision"] != "reject" or not item["replace"]:
        return False
    candidate = verdict["candidate"]
    span = verdict["output"].partition("|")[2].strip()
    if not span or candidate.count(span) != 1 or candidate.count(item["with"]) != 1:
        return False
    start = candidate.index(span)
    end = start + len(span)
    offset = candidate.index(item["with"])
    for tag, _, _, a, b in SequenceMatcher(None, item["replace"], item["with"], autojunk=False).get_opcodes():
        if tag == "equal":
            continue
        if a == b:
            if start < offset + a < end:
                return True
        elif max(start, offset + a) < min(end, offset + b):
            return True
    return False


if __name__ == "__main__":
    argparse.ArgumentParser(description=__doc__).parse_args()
    verdicts = json.loads((study.EVIDENCE / "judge-results.json").read_text())["cases"]
    output = {item["id"]: locate(item, verdicts[item["id"]]) for item, _ in study.controls()}
    print(json.dumps(output, indent=2))
